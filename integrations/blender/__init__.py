import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, IntProperty, FloatProperty, EnumProperty
from multiprocessing import Pool
import mathutils
import os
import json
import requests
import time
import threading
import textwrap
import struct
import re

# plugin info
bl_info = {
    "name": "CloudRF 3D",
    "description": "Simulate RF propagation using the CloudRF 3D API",
    "author": "CloudRF.com",
    "version": (1, 1, 0),
    "blender": (3, 6, 0),
    "category": "Import-Export"
}

# build number shown at the top of the CloudRF panel. bump it with every
# change so a successful Reload Scripts is obvious in the UI
BUILD = 7


def manifest_version():
    try:
        import tomllib
        with open(os.path.join(os.path.dirname(__file__), "blender_manifest.toml"), "rb") as f:
            return tomllib.load(f).get("version", "?")
    except Exception:
        return ".".join(str(v) for v in bl_info["version"])


# set in register(), so the panel shows when this code was last (re)loaded
loaded_at = ""
plugin_version = ""

# vertical offset (metres, Blender Z-up) applied to imported heatmap results
# so they render above the original model instead of clipping into it
RESULT_Z_OFFSET = 0.1

# minimum near clip distance (metres) for cameras and 3D viewports once a
# result is loaded; a larger clip_start improves depth precision and
# reduces z-fighting between the heatmap and the model
RESULT_CLIP_START = 0.1

# every simulation result is imported into this collection, replacing the
# previous one. older plugin versions used "cloudRF 3D Result <timestamp>",
# so anything with this prefix counts as a previous result
RESULT_COLLECTION_NAME = "cloudRF 3D Result"


def remove_previous_results():
    old = [c for c in bpy.data.collections if c.name.startswith(RESULT_COLLECTION_NAME)]
    for collection in old:
        meshes, materials = set(), set()
        for obj in list(collection.all_objects):
            if obj.type == 'MESH' and obj.data:
                meshes.add(obj.data)
                materials.update(m for m in obj.data.materials if m)
            bpy.data.objects.remove(obj, do_unlink = True)
        for child in list(collection.children_recursive):
            bpy.data.collections.remove(child)
        bpy.data.collections.remove(collection)

        # free the imported data blocks too, but only ones nothing else uses
        for mesh in meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        for mat in materials:
            if mat.users == 0:
                images = set()
                if mat.node_tree:
                    images = {n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image}
                bpy.data.materials.remove(mat)
                for img in images:
                    if img.users == 0:
                        bpy.data.images.remove(img)


def raise_clip_start(context, minimum = RESULT_CLIP_START):
    # never lower a clip_start the user has already set higher
    for obj in context.scene.objects:
        if obj.type == 'CAMERA' and obj.data.clip_start < minimum:
            obj.data.clip_start = minimum
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type == 'VIEW_3D' and space.clip_start < minimum:
                    space.clip_start = minimum

templates = {
    "Large": {
        "frq": 2232.0,
        "txw": 2.0,
        "pos": {
            "x": 1.0,
            "y": 2.0,
            "z": 3.0
        },
        "antenna": {
            "ant": 1,
            "hbw": 0,
            "vbw": 0,
            "txg": 2.15,
            "txl": 0.0,
            "fbr": 0
        }
    },
    "Medium": {
        "frq": 2232.0,
        "txw": 1.0,
        "pos": {
            "x": 1.0,
            "y": 2.0,
            "z": 3.0
        },
        "antenna": {
            "ant": 1,
            "hbw": 0,
            "vbw": 0,
            "txg": 2.15,
            "txl": 0.0,
            "fbr": 0
        }
    },
    "Small": {
        "frq": 2232.0,
        "txw": 0.5,
        "pos": {
            "x": 1.0,
            "y": 2.0,
            "z": 3.0
        },
        "antenna": {
            "ant": 1,
            "hbw": 0,
            "vbw": 0,
            "txg": 2.15,
            "txl": 0.0,
            "fbr": 0
        }
    }
}


# names of the templates which were imported from JSON, as opposed to the
# built in ones above. these are saved to disk so they survive a restart
user_templates = set()


def user_templates_path():
    config = bpy.utils.user_resource("CONFIG", path = "cloudrf", create = True)
    return os.path.join(config, "templates.json")


# imported templates only live in memory, so restore the ones from previous
# sessions when the plugin loads
def load_user_templates():
    path = user_templates_path()

    try:
        with open(path, 'r') as file:
            saved = json.load(file)
    except FileNotFoundError:
        return
    except (json.JSONDecodeError, OSError) as error:
        print(f"CloudRF: could not read saved templates from {path}: {error}")
        return

    for name, template in saved.items():
        templates[name] = template
        user_templates.add(name)


def save_user_templates():
    path = user_templates_path()

    try:
        with open(path, 'w') as file:
            json.dump({name: templates[name] for name in user_templates}, file, indent = 4)
    except OSError as error:
        print(f"CloudRF: could not save templates to {path}: {error}")
        return False

    return True


# the transmitters among the given objects, e.g. the current selection
def transmitter_objects(objects):
    return [obj for obj in objects if hasattr(obj, "transmitter_properties") and "Transmitter" in obj.name]


# an operator run from the sidebar does not redraw the other editors by itself,
# so the properties tab would keep showing the old radio settings until it is
# nudged. tag the changed objects and ask every editor to redraw
def refreshUI(context, objects):
    for obj in objects:
        obj.update_tag()

    for window in context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()


# copy the radio settings of a template onto an existing transmitter
def applyTemplate(obj, data):
    obj.transmitter_properties.frq = data["frq"]
    obj.transmitter_properties.txw = data["txw"]
    obj.transmitter_properties.ant = data["antenna"]["ant"]
    obj.transmitter_properties.ant_custom = data["antenna"]["ant"] == 0
    obj.transmitter_properties.hbw = data["antenna"]["hbw"]
    obj.transmitter_properties.vbw = data["antenna"]["vbw"]
    obj.transmitter_properties.txg = data["antenna"]["txg"]
    obj.transmitter_properties.txl = data["antenna"]["txl"]
    obj.transmitter_properties.fbr = data["antenna"]["fbr"]


def addTransmitter(data, location = (0, 0, 0)):
    bpy.ops.object.empty_add(location = location)
    
    obj = bpy.context.active_object
    obj.name = "Transmitter"

    applyTemplate(obj, data)

    obj.empty_display_type = "IMAGE"
    obj.data = bpy.data.images.load(f"{os.path.dirname(__file__)}/CloudRF_tx.png", check_existing=True)

last_sim_time = 0.0

def templates_to_enum(scene, context):
    items=[
    ]

    for name in templates:

        items.append((name, name, name))

    return items

class addTransmitterFromTemplateOperator(bpy.types.Operator):
    bl_label = "Add Radio"
    bl_idname = "cloudrf.add_transmitter_template_add"
    bl_description = "Add a radio marker at the 3D cursor using the chosen template"
    bl_options = {"REGISTER", "UNDO"}

    action: bpy.props.EnumProperty(name="cloudrf.templates", items=templates_to_enum)

    def execute(self, context):
        template_name = self.properties.action

        if not template_name in templates:
            self.report({"ERROR"}, f"Could not find template with name: {template_name}")
            return {"CANCELLED"}

        addTransmitter(templates[template_name], context.scene.cursor.location.copy())

        return {"FINISHED"}


# apply a template to transmitters which already exist in the scene
class applyTemplateToSelectedOperator(bpy.types.Operator):
    bl_label = "Apply To Selected"
    bl_idname = "cloudrf.apply_template_selected"
    bl_description = "Apply the radio settings of a template to the selected transmitters"

    action: bpy.props.EnumProperty(name="cloudrf.templates", items=templates_to_enum)

    def execute(self, context):
        template_name = self.properties.action

        if not template_name in templates:
            self.report({"ERROR"}, f"Could not find template with name: {template_name}")
            return {"CANCELLED"}

        selected = transmitter_objects(context.selected_objects)

        if not selected:
            self.report({"ERROR"}, "Please select at least one transmitter to apply the template to!")
            return {"CANCELLED"}

        for obj in selected:
            applyTemplate(obj, templates[template_name])

        refreshUI(context, selected)

        self.report({"INFO"}, f"Applied template {template_name} to {len(selected)} transmitter(s)")

        return {"FINISHED"}



# settings for json file for request to API

# fields for settings
class properties(bpy.types.PropertyGroup):    
    max_reflections: bpy.props.IntProperty(name = "Max Reflections",
    min = 1,
    default = 5,
    max = 10,
    description = "The maximum number of times a photon can be reflected"
    )
    
    res: bpy.props.FloatProperty(name = "Resolution",
    min = 0.1,
    default = 0.5,
    max = 300.0,
    description = "Resolution in metres for produced output. Lower number means a more precise simulation, but will take longer"
    )
      
    materials_initialised: bpy.props.BoolProperty(default = False)

    phase: bpy.props.BoolProperty(name = "Phase",
    default = False,
    description = "Include phase in the 3D simulation (sends 3d.phase = true)"
    )

    api_key: bpy.props.StringProperty(name = "API Key",
    description = "Paste your API key in here",
    subtype = "PASSWORD"
    )
    
    server_address: bpy.props.StringProperty(name = "Server Address",
    description = "The server address to connect to for the simulation",
    default = "https://api.cloudrf.com"
    )

    colour_key: bpy.props.StringProperty(name = "Colour Key",
    default = "LTE"
    )
       
    template_name: bpy.props.StringProperty(name = "Path",
    description = "Where is your settings template located?"
    )

    uploading_model: bpy.props.BoolProperty(name = "Uploading Model")
    
# import button
class importOperator(bpy.types.Operator):
    
    # settings
    bl_idname = "cloudrf.import"
    bl_label = "Import"
    
    def execute(self, context):
        scene = context.scene
        
        filepath = scene.props.template_name
        
        if len(filepath) < 1:
            self.report({"ERROR"}, "Please specify a filepath for the template!")
            return {"CANCELLED"}
        
        try:
            with open(filepath, 'r') as file:
                data = json.load(file)

                name = data["template"]["name"]
                transmitter_data = {
                    "frq": data["transmitter"]["frq"],
                    "txw": data["transmitter"]["txw"],
                    "pos": {
                        "x": 1.0,
                        "y": 2.0,
                        "z": 3.0
                    },
                    "antenna": {
                        "ant": data["antenna"]["ant"],
                        "hbw": data["antenna"]["hbw"],
                        "vbw": data["antenna"]["vbw"],
                        "txg": data["antenna"]["txg"],
                        "txl": data["antenna"]["txl"],
                        "fbr": data["antenna"]["fbr"],
                    }
                }

                templates[name] = transmitter_data
                user_templates.add(name)

                # scene.props.max_reflections = data["3d"]["max_reflections"]
                # scene.props.res = data["output"]["res"]
            
        except FileNotFoundError:
            self.report({"ERROR"}, "File not found please specify a valid file!")
            return {"CANCELLED"}
        except json.JSONDecodeError:
            self.report({"ERROR"}, "Please provide a valid JSON format!")
            return {"CANCELLED"}
        except KeyError as error:
            self.report({"ERROR"}, f"Template has no {error} setting, is this a CloudRF template?")
            return {"CANCELLED"}
        
        if not save_user_templates():
            self.report({"WARNING"}, "Template imported but could not be saved for future sessions, see the system console")

        # a template is only used by the transmitters it is applied to, so apply
        # it to the selection rather than leaving them on their old settings
        selected = transmitter_objects(context.selected_objects)

        for obj in selected:
            applyTemplate(obj, templates[name])

        refreshUI(context, selected)

        if selected:
            self.report({"INFO"}, f"Imported template {name} and applied it to {len(selected)} selected transmitter(s)")
        else:
            self.report({"INFO"}, f"Successfully imported template {name}!\n{templates[name]}\nAdd a transmitter with it from Add > Transmitters, or select transmitters and use Apply To Selected")
        
        return {"FINISHED"}
    
# browse button
class browseOperator(bpy.types.Operator):
    bl_idname = "cloudrf.browse"
    bl_label = "Browse"
    
    filepath: bpy.props.StringProperty(subtype = "FILE_PATH")
    
    def execute(self, context):
        context.scene.props.template_name = self.filepath
        return {"FINISHED"}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}
    
    def draw(self, context):
        pass

# upload button
class uploadOperator(bpy.types.Operator):
    
    # settings for the button
    bl_idname = "cloudrf.upload"
    bl_label = "Upload model"
    
    @classmethod
    def poll(cls, context):
        cooldown_period = 5 # cooldown of 5 seconds on upload/simulate button
        return time.time() - last_sim_time >= cooldown_period

    # when the button is pressed
    def execute(self, context):
        
        # get the scene
        scene = context.scene
        
        for view_layer in scene.view_layers:
                for layer_collection in view_layer.layer_collection.children:
                    if layer_collection.collection.ignore_properties and layer_collection.collection.ignore_properties.ignore:
                        layer_collection.exclude = True


        # access last click time and update it
        global last_sim_time
        last_sim_time = time.time()
        
        # urls for the API
        model_upload_url = scene.props.server_address + "/3d/model/upload"
        
        # perform check to the server
        
        try:
            pass
            #requests.get(scene.props.server_address)
        except requests.exceptions.HTTPError:
            self.report({"ERROR"}, "Please specify a valid server address!")
            return {"CANCELLED"}
        except requests.exceptions.RequestException:
            self.report({"ERROR"}, "Please specify a valid server address!")
            return {"CANCELLED"}
        
        # minimum length check for API key
        if len(scene.props.api_key) < 1:
            self.report({"ERROR"}, "Please provide a valid API key!")
            return {"CANCELLED"} 
        
        # json for API key
        key_json = {
            "key": scene.props.api_key
        }
        
        # the file must be saved to get its filepath
        try:
            # export the current file to a glb file
            filepath = os.path.dirname(bpy.data.filepath) + "/crf_blender_plugin_model.glb"
            bpy.ops.export_scene.gltf(
                export_format = 'GLB',
                use_visible = True,
                filepath = filepath,
                check_existing = False
            )
        
            # post the recently made glb file
            with open(filepath, "rb") as file:
                res = requests.post(model_upload_url, headers = api_headers(scene.props.api_key), files = {"file": file}, verify = False)
                self.report({"INFO"}, "Response: \n" + str(res.content))
        except:
            self.report({"ERROR"}, "An unexpected error occured!. Ensure the model is saved somewhere that it can be accessed!")
            return {"CANCELLED"}

        return {"FINISHED"}


# simulate button
# sent with every request to the CloudRF API
USER_AGENT = "CloudRF Blender plugin"


def api_headers(api_key):
    return {"key": api_key, "User-Agent": USER_AGENT}


# default RF properties for common model materials. a material in the model
# matches an entry when its name equals one of the keys, or contains it (the
# longest key wins, so "Car_glass" beats "Glass"). case is ignored, as is
# Blender's ".001" duplicate suffix
DEFAULT_MATERIALS = [
    {"keys": ["Brick"], "reflection_loss": 9.5, "transmission_loss": 10.0},
    {"keys": ["Glass"], "reflection_loss": 7.5, "transmission_loss": 5.0},
    {"keys": ["Wood"], "reflection_loss": 15.0, "transmission_loss": 5.0},
    {"keys": ["Plasterboard"], "reflection_loss": 15.0, "transmission_loss": 4.0},
    {"keys": ["Roof_tiles"], "reflection_loss": 10.0, "transmission_loss": 10.0},
    {"keys": ["Concrete"], "reflection_loss": 8.0, "transmission_loss": 17.0},
    {"keys": ["Grass"], "reflection_loss": 4.5, "transmission_loss": 90.0},
    {"keys": ["Asphalt"], "reflection_loss": 9.0, "transmission_loss": 90.0},
    {"keys": ["Car_body"], "reflection_loss": 0.5, "transmission_loss": 90.0},
    {"keys": ["Car_glass"], "reflection_loss": 7.5, "transmission_loss": 4.0},
    {"keys": ["Tyre"], "reflection_loss": 10.0, "transmission_loss": 90.0},
]

# diffusion sent for every material (not editable in the table)
MATERIAL_DIFFUSION = 3.0

MODEL_FILE_NAME = "crf_blender_plugin_model.glb"

# outcome of the last material scan, shown in the materials panel
material_scan = None


def model_glb_path():
    return os.path.join(os.path.dirname(bpy.data.filepath), MODEL_FILE_NAME)


def load_default_materials(scene):
    scene.cloudrf_materials.clear()
    for data in DEFAULT_MATERIALS:
        entry = scene.cloudrf_materials.add()
        entry.keys = ", ".join(data["keys"])
        entry.reflection_loss = data["reflection_loss"]
        entry.transmission_loss = data["transmission_loss"]
    scene.cloudrf_materials_index = 0
    scene.props.materials_initialised = True


# read material names straight from a GLB file's JSON chunk
def glb_material_names(path):
    with open(path, "rb") as file:
        magic, _version, _length = struct.unpack("<4sII", file.read(12))
        if magic != b"glTF":
            raise ValueError("not a GLB file")
        chunk_length, chunk_type = struct.unpack("<II", file.read(8))
        if chunk_type != 0x4E4F534A: # "JSON"
            raise ValueError("GLB has no JSON chunk")
        gltf = json.loads(file.read(chunk_length))
    return sorted({m["name"] for m in gltf.get("materials", []) if m.get("name")})


# materials on visible meshes, used when the model has not been uploaded yet
def scene_material_names(context):
    names = set()
    for obj in context.visible_objects:
        if obj.type != "MESH" or any(c.name.startswith(RESULT_COLLECTION_NAME) for c in obj.users_collection):
            continue
        names.update(slot.material.name for slot in obj.material_slots if slot.material)
    return sorted(names)


# the model's material names and where they came from
def model_material_names(context):
    path = model_glb_path()
    if bpy.data.filepath and os.path.exists(path):
        try:
            return glb_material_names(path), "uploaded model"
        except (OSError, ValueError, struct.error) as error:
            print(f"CloudRF: could not read materials from {path}: {error}")
    return scene_material_names(context), "scene (model not uploaded yet)"


def normalise_material_name(name):
    return re.sub(r"\.\d{3}$", "", name).strip().lower()


def entry_keys(entry):
    return [k.strip() for k in entry.keys.split(",") if k.strip()]


# map each model material name to the index of the table entry it matches
def match_materials(names, entries):
    keyed = [(normalise_material_name(key), index) for index, entry in enumerate(entries) for key in entry_keys(entry)]
    matches = {}
    for name in names:
        normalised = normalise_material_name(name)
        exact = [index for key, index in keyed if key == normalised]
        if exact:
            matches[name] = exact[0]
            continue
        partial = [(len(key), -index) for key, index in keyed if key and key in normalised]
        if partial:
            matches[name] = -max(partial)[1]
    return matches


# scan the model, remember the outcome for the panel and build the request
# "materials" array. each matched entry is sent with its own keys plus the
# exact model material names it matched, so the server can't miss them
def scan_materials(context):
    global material_scan
    entries = list(context.scene.cloudrf_materials)
    names, source = model_material_names(context)
    matches = match_materials(names, entries)

    request = []
    for index, entry in enumerate(entries):
        matched = sorted(name for name, i in matches.items() if i == index)
        if not matched:
            continue
        keys = list(dict.fromkeys(entry_keys(entry) + matched))
        request.append({
            "keys": keys,
            "reflection_loss": round(entry.reflection_loss, 3),
            "transmission_loss": round(entry.transmission_loss, 3),
            "diffusion": MATERIAL_DIFFUSION,
        })

    material_scan = {
        "source": source,
        "rows": [(name, entry_keys(entries[matches[name]])[0] if name in matches and entry_keys(entries[matches[name]]) else None) for name in names],
        "matched": len(matches),
        "total": len(names),
    }
    return request

# seconds to wait for each API request
SIM_TIMEOUT = 120

# state of the simulation that is running, or the last one. a fresh dict is
# made per run so a stale worker thread can never write into a newer run
sim_state = {"running": False}

# outcome of the last simulation, shown in the report dialog
last_result = None


def build_transmitters():
    transmitters = []

    for obj in bpy.data.objects:
        if hasattr(obj, "transmitter_properties") and "Transmitter" in obj.name:
            blender_up = mathutils.Vector((0.0, 0.0, 1.0))
            blender_fwd = mathutils.Vector((0.0, -1.0, 0.0))

            blender_up.rotate(obj.rotation_euler)
            blender_fwd.rotate(obj.rotation_euler)

            if obj.transmitter_properties.ant_custom:
                antenna = {
                    "ant": 0,
                    "hbw": obj.transmitter_properties.hbw,
                    "vbw": obj.transmitter_properties.vbw,
                    "txg": obj.transmitter_properties.txg,
                    "txl": obj.transmitter_properties.txl,
                    "fbr": obj.transmitter_properties.fbr
                }
            else:
                antenna =  {
                    "ant": obj.transmitter_properties.ant,
                    "txg": obj.transmitter_properties.txg,
                    "txl": obj.transmitter_properties.txl,
                }

            transmitters.append({
                "frq": obj.transmitter_properties.frq,
                "txw": obj.transmitter_properties.txw,
                "pos": {
                    "x": obj.location.x,
                    "y": obj.location.z,
                    "z": -obj.location.y
                },
                "up": {
                    "x": blender_up.x,
                    "y": blender_up.z,
                    "z": -blender_up.y
                },
                "fwd": {
                    "x": blender_fwd.x,
                    "y": blender_fwd.z,
                    "z": -blender_fwd.y
                },
                "antenna": antenna
            })

    return transmitters


def api_error_message(response, data):
    if isinstance(data, dict):
        for key in ("error", "message", "detail"):
            if data.get(key):
                return f"HTTP {response.status_code}: {data[key]}"
    text = (response.text or "").strip()
    return f"HTTP {response.status_code}: {text[:500] or response.reason}"


# runs in a background thread: must not touch bpy, only the state dict
def simulate_worker(state, url, headers, body, file_path):
    try:
        state["stage"] = "Simulating on server"
        state["progress"] = 0.15
        response = requests.post(url, json = body, headers = headers, timeout = SIM_TIMEOUT, verify = False)
        state["http_status"] = response.status_code

        try:
            data = response.json()
        except ValueError:
            data = None
        state["response"] = data

        if not response.ok or not isinstance(data, dict) or data.get("error"):
            state["error"] = api_error_message(response, data)
            return

        file_url = data.get("model_file_uncompressed")
        if not file_url:
            state["error"] = "The response did not include a result model (model_file_uncompressed)"
            return

        state["stage"] = "Downloading result"
        state["progress"] = 0.7
        download = requests.get(file_url, headers = headers, timeout = SIM_TIMEOUT, verify = False)
        if not download.ok:
            state["error"] = "Result download failed: " + api_error_message(download, None)
            return

        with open(file_path, "wb") as file:
            file.write(download.content)
        state["download_bytes"] = len(download.content)

        state["stage"] = "Importing result"
        state["progress"] = 0.9
    except requests.exceptions.Timeout:
        state["error"] = f"The server did not respond within {SIM_TIMEOUT} seconds"
    except requests.exceptions.RequestException as error:
        state["error"] = f"Network error: {error}"
    except Exception as error:
        state["error"] = f"{type(error).__name__}: {error}"
    finally:
        state["done"] = True


def format_value(value):
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    if isinstance(value, list):
        return f"{len(value)} items"
    text = str(value)
    return text if len(text) <= 90 else text[:87] + "..."


# flatten the response JSON (one level of nesting) into label rows
def response_rows(data):
    rows = []
    if not isinstance(data, dict):
        return rows
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if sub_value is not None and not isinstance(sub_value, dict):
                    rows.append((f"{key}.{sub_key}", format_value(sub_value)))
        else:
            rows.append((key, format_value(value)))
    return rows


def import_result(context, file_path):
    old_objs = set(context.scene.objects)

    # import the downloaded glb file into the current scene
    bpy.ops.import_scene.gltf(filepath = file_path)

    imported_objs = set(context.scene.objects) - old_objs

    # replace the previous result instead of stacking a new layer each run
    remove_previous_results()
    collection = bpy.data.collections.new(RESULT_COLLECTION_NAME)
    context.scene.collection.children.link(collection)
    collection.ignore_properties.ignore = True
    for obj in imported_objs:
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        collection.objects.link(obj)
        # lift the heatmap slightly above the source model to prevent
        # z-fighting/clipping; only top-level objects, so children
        # aren't offset twice through their parent
        if obj.parent not in imported_objs:
            obj.location.z += RESULT_Z_OFFSET

    raise_clip_start(context)

    return len(imported_objs)


def redraw_all(context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()


class simulateOperator(bpy.types.Operator):
    
    # settings for the button
    bl_idname = "cloudrf.simulate"
    bl_label = "Simulate"
    bl_description = "Run a 3D simulation with the radios in the scene"

    _timer = None
    
    @classmethod
    def poll(cls, context):
        cooldown_period = 5 # cooldown of 5 seconds on upload/simulate button
        return not sim_state["running"] and time.time() - last_sim_time >= cooldown_period

    def execute(self, context):
        return self.invoke(context, None)

    # when the button is pressed
    def invoke(self, context, event):
        global last_sim_time, sim_state, last_result

        scene = context.scene
        
        for view_layer in scene.view_layers:
                for layer_collection in view_layer.layer_collection.children:
                    if layer_collection.collection.ignore_properties and layer_collection.collection.ignore_properties.ignore:
                        layer_collection.exclude = True

        last_sim_time = time.time()
        
        # minimum length check for API key
        if len(scene.props.api_key) < 1:
            return self.fail_early(context, "Please provide a valid API key!")

        transmitters = build_transmitters()
        if not transmitters:
            return self.fail_early(context, "There are no radios in the scene. Use Add radio first")

        # request settings for API
        request_options = {
            "transmitters": transmitters,
            "3d": {
                "input_file": "crf_blender_plugin_model.glb",
                "max_reflections": scene.props.max_reflections,
                "phase": scene.props.phase
            },
            "output": {
                "res": scene.props.res,
                "col": scene.props.colour_key + ".dBm",
                "out": 2, # Received power
            },
            "receiver": {
                "rxs": -105.0,
                "rxg": 0.0
            }
        }
        materials = scan_materials(context)
        if materials:
            request_options["materials"] = materials

        self.report({"INFO"}, "Request: \n" + str(request_options))

        sim_state = {
            "running": True,
            "done": False,
            "stage": "Sending request",
            "progress": 0.05,
            "started": time.time(),
            "server": scene.props.server_address,
            "transmitters": len(transmitters),
            "materials": f"{material_scan['matched']} of {material_scan['total']} matched",
            "file_path": bpy.data.filepath + "result.glb",
        }
        last_result = None

        threading.Thread(
            target = simulate_worker,
            args = (sim_state, scene.props.server_address + "/3d", api_headers(scene.props.api_key), request_options, sim_state["file_path"]),
            daemon = True,
        ).start()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.25, window = context.window)
        wm.progress_begin(0, 100)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def fail_early(self, context, message):
        global last_result
        last_result = {"ok": False, "message": message, "rows": []}
        self.report({"ERROR"}, message)
        show_report()
        return {"CANCELLED"}

    def modal(self, context, event):
        if event.type != "TIMER":
            return {"PASS_THROUGH"}

        state = sim_state
        elapsed = time.time() - state["started"]
        context.window_manager.progress_update(int(state["progress"] * 100))
        if context.workspace:
            context.workspace.status_text_set(f"CloudRF: {state['stage']}... {elapsed:.0f}s")
        redraw_all(context)

        if not state["done"]:
            return {"PASS_THROUGH"}

        return self.finish(context, state)

    def finish(self, context, state):
        global last_result

        imported = 0
        if not state.get("error"):
            try:
                imported = import_result(context, state["file_path"])
            except Exception as error:
                state["error"] = f"Could not import the result: {error}"

        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        wm.progress_end()
        if context.workspace:
            context.workspace.status_text_set(None)
        state["running"] = False

        rows = [
            ("Server", state["server"]),
            ("Radios", str(state["transmitters"])),
            ("Materials", state["materials"]),
            ("Total time", f"{time.time() - state['started']:.1f}s"),
        ]
        if "http_status" in state:
            rows.append(("HTTP status", str(state["http_status"])))
        if "download_bytes" in state:
            rows.append(("Result size", f"{state['download_bytes'] / 1024:.0f} KB"))
        if not state.get("error"):
            rows.append(("Objects imported", str(imported)))
        rows += [("", "")] + response_rows(state.get("response")) if state.get("response") else []

        if state.get("error"):
            message = state["error"]
            self.report({"ERROR"}, "Simulation failed: " + message)
        else:
            elapsed_s = (state.get("response") or {}).get("elapsed_s", "?")
            message = f"Simulation complete in {elapsed_s} seconds"
            self.report({"INFO"}, message)
        if state.get("response") is not None:
            self.report({"INFO"}, "Response: \n" + str(state["response"]))

        last_result = {"ok": not state.get("error"), "message": message, "rows": rows}
        redraw_all(context)
        show_report()

        return {"CANCELLED"} if state.get("error") else {"FINISHED"}


def show_report():
    try:
        bpy.ops.cloudrf.simulation_report("INVOKE_DEFAULT")
    except RuntimeError as error:
        print(f"CloudRF: could not show the simulation report: {error}")


# dialog with the outcome of the last simulation and the response metadata
class simulationReportOperator(bpy.types.Operator):
    bl_idname = "cloudrf.simulation_report"
    bl_label = "CloudRF Simulation"
    bl_description = "Show the outcome of the last simulation"

    @classmethod
    def poll(cls, context):
        return last_result is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width = 480)

    def execute(self, context):
        return {"FINISHED"}

    def draw(self, context):
        l = self.layout
        result = last_result

        header = l.box()
        if result["ok"]:
            header.label(text = "Success", icon = "CHECKMARK")
        else:
            header.label(text = "Error", icon = "ERROR")
        for line in textwrap.wrap(result["message"], 70) or [""]:
            header.label(text = line)

        if result["rows"]:
            grid = l.column(align = True)
            for key, value in result["rows"]:
                if not key:
                    grid.separator()
                    grid.label(text = "Response", icon = "TEXT")
                    continue
                row = grid.split(factor = 0.38)
                row.label(text = key)
                row.label(text = value)


class materialEntry(bpy.types.PropertyGroup):
    keys: bpy.props.StringProperty(name = "Keys",
    description = "Material names this entry applies to, separated by commas. A model material matches if its name equals or contains a key"
    )
    reflection_loss: bpy.props.FloatProperty(name = "Reflection loss",
    min = 0.0, max = 90.0, default = 3.0, precision = 1,
    description = "Loss in dB for each reflection off this material. Metal has low loss"
    )
    transmission_loss: bpy.props.FloatProperty(name = "Transmission loss",
    min = 0.0, max = 90.0, default = 15.0, precision = 1,
    description = "Loss in dB per metre when passing through this material. Metal is very high"
    )


class CLOUDRF_UL_materials(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor = 0.4, align = True)
        row.prop(item, "keys", text = "", emboss = False)
        values = row.row(align = True)
        values.prop(item, "reflection_loss", text = "")
        values.prop(item, "transmission_loss", text = "")


class CLOUDRF_OT_material_add(bpy.types.Operator):
    bl_idname = "cloudrf.material_add"
    bl_label = "Add Material"
    bl_description = "Add a row to the materials table"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        entry = scene.cloudrf_materials.add()
        entry.keys = "New_material"
        scene.cloudrf_materials_index = len(scene.cloudrf_materials) - 1
        return {"FINISHED"}


class CLOUDRF_OT_material_remove(bpy.types.Operator):
    bl_idname = "cloudrf.material_remove"
    bl_label = "Remove Material"
    bl_description = "Remove the selected row from the materials table"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        return 0 <= scene.cloudrf_materials_index < len(scene.cloudrf_materials)

    def execute(self, context):
        scene = context.scene
        scene.cloudrf_materials.remove(scene.cloudrf_materials_index)
        scene.cloudrf_materials_index = min(scene.cloudrf_materials_index, len(scene.cloudrf_materials) - 1)
        return {"FINISHED"}


class CLOUDRF_OT_materials_reset(bpy.types.Operator):
    bl_idname = "cloudrf.materials_reset"
    bl_label = "Reset Materials"
    bl_description = "Replace the materials table with the CloudRF defaults"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        if len(context.scene.cloudrf_materials) == 0:
            return self.execute(context)
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        load_default_materials(context.scene)
        return {"FINISHED"}


class CLOUDRF_OT_materials_scan(bpy.types.Operator):
    bl_idname = "cloudrf.materials_scan"
    bl_label = "Detect Model Materials"
    bl_description = "List the model's materials and which table row each one matches"

    def execute(self, context):
        scan_materials(context)
        self.report({"INFO"}, f"Matched {material_scan['matched']} of {material_scan['total']} materials from the {material_scan['source']}")
        return {"FINISHED"}


class CLOUDRF_PT_materials(bpy.types.Panel):
    bl_label = "3D materials"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CloudRF"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        l = self.layout
        scene = context.scene

        header = l.split(factor = 0.4)
        header.label(text = "Keys")
        cols = header.row()
        cols.label(text = "Refl")
        cols.label(text = "Trans")

        row = l.row()
        row.template_list("CLOUDRF_UL_materials", "", scene, "cloudrf_materials", scene, "cloudrf_materials_index", rows = 6)
        side = row.column(align = True)
        side.operator(CLOUDRF_OT_material_add.bl_idname, text = "", icon = "ADD")
        side.operator(CLOUDRF_OT_material_remove.bl_idname, text = "", icon = "REMOVE")
        side.separator()
        side.operator(CLOUDRF_OT_materials_reset.bl_idname, text = "", icon = "LOOP_BACK")

        l.label(text = "Refl / Trans loss in dB. Matched rows are sent with Simulate")
        l.operator(CLOUDRF_OT_materials_scan.bl_idname, icon = "VIEWZOOM")

        if material_scan is not None:
            box = l.box()
            box.label(text = f"{material_scan['matched']} of {material_scan['total']} matched ({material_scan['source']})")
            for name, key in material_scan["rows"]:
                line = box.split(factor = 0.55)
                line.label(text = name, icon = "MATERIAL")
                line.label(text = key or "default", icon = "CHECKMARK" if key else "BLANK1")


@bpy.app.handlers.persistent
def seed_materials_on_load(*_args):
    for scene in bpy.data.scenes:
        if not scene.props.materials_initialised:
            load_default_materials(scene)


def seed_materials_timer():
    try:
        seed_materials_on_load()
    except Exception as error:
        print(f"CloudRF: could not load default materials: {error}")
    return None


MATERIAL_CLASSES = (
    materialEntry,
    CLOUDRF_UL_materials,
    CLOUDRF_OT_material_add,
    CLOUDRF_OT_material_remove,
    CLOUDRF_OT_materials_reset,
    CLOUDRF_OT_materials_scan,
)

# cloud rf panel (press N to open)
class MainPanel(bpy.types.Panel):
    
    # settings
    bl_idname = "panel_main"
    bl_label = "3D simulation API"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CloudRF"
    
    def draw(self, context):
        l = self.layout
        scene = context.scene
        
        l.label(text = f"v{plugin_version} build {BUILD}  (loaded {loaded_at})", icon = "INFO")

        # draw all options in cloud rf panel
        l.operator_menu_enum(addTransmitterFromTemplateOperator.bl_idname, "action", text = "Add radio", icon = "ADD")
        l.operator(uploadOperator.bl_idname)
        l.operator(simulateOperator.bl_idname)

        if sim_state["running"]:
            box = l.box()
            elapsed = time.time() - sim_state["started"]
            box.label(text = f"{sim_state['stage']}... {elapsed:.0f}s", icon = "TIME")
            box.progress(factor = sim_state["progress"], type = "BAR")
        elif last_result is not None:
            l.operator(simulationReportOperator.bl_idname, text = "Last result: " + ("success" if last_result["ok"] else "error"),
                icon = "CHECKMARK" if last_result["ok"] else "ERROR")
        l.prop(scene.props, "api_key")
        l.prop(scene.props, "server_address")
        
# settings panel for frequency, power etc.
class SettingsPanel(bpy.types.Panel):
    
    # settings
    bl_idname = "panel_settings"
    bl_label = "3D RF settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CloudRF"
    
    def draw(self, context):
        l = self.layout
        scene = context.scene
        
        l.prop(scene.props, "max_reflections")
        l.prop(scene.props, "res")
        l.prop(scene.props, "phase")
        l.prop(scene.props, "colour_key")
    
# IO panel for JSON templates    
class IOPanel(bpy.types.Panel):
    
    # settings
    bl_idname = "panel_io"
    bl_label = "CloudRF radio template"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CloudRF"
    
    def draw(self, context):
        l = self.layout
        scene = context.scene
    
        l.operator(importOperator.bl_idname)
        l.prop(scene.props, "template_name")
        l.operator(browseOperator.bl_idname)
        l.operator_menu_enum(applyTemplateToSelectedOperator.bl_idname, "action", text = "Apply To Selected")

class collectionIgnoreProperties(bpy.types.PropertyGroup):
    ignore: bpy.props.BoolProperty(
        name = "Ignore",
        default = False,
        description = "If this property is true, the collection will not be exported to the CloudRF 3D API"
    )

# transmitter properties
class transmitterProperties(bpy.types.PropertyGroup):
    frq: bpy.props.FloatProperty(
    name = "Frequency (MHz)",
    default = 2232.0,
    description = "Center frequency in megahertz"
    )
    
    txw: bpy.props.FloatProperty(name = "Power (W)",
    default = 2.0,
    description = "Transmitter power in watts before the antenna"
    )
    
    ant: bpy.props.IntProperty(name = "Antenna",
    min = 1,
    default = 1,
    description = "Antenna pattern code"
    )
    
    hbw: bpy.props.FloatProperty(name = "Horizontal Beam Width (degrees)",
    default = 120,
    min = 1,
    max = 180,
    description = "Custom antenna horizontal beamwidth in degrees"
    )
    
    vbw: bpy.props.FloatProperty(name = "Vertical Beam Width (degrees)",
    default = 120,
    min = 1,
    max = 180,
    description = "Custom antenna vertical beamwidth in degrees"
    )
    
    txg: bpy.props.FloatProperty(name = "Gain (dBi)",
    default = 2.15,
    description = "Transmitter antenna gain in dBi.\nA half-wave dipole has a gain of 2.15dBi.\nA mobile phone is 0 to 2dBi, depending on the frequency"
    )
    
    txl: bpy.props.FloatProperty(name = "Feeder Loss (dB)",
    default = 0,
    description = "Feeder loss in dB. A long feeder has more loss. Loss varies by material and wavelength e.g. LMR-400"
    )
    
    fbr: bpy.props.FloatProperty(name = "Front-Back Ratio (dB)",
    default = 9,
    description = "Front-to-back ratio measured in dB. A highly directional antenna will have a high FBR"
    )

    ant_custom: bpy.props.BoolProperty(name = "Use Custom Pattern",
    default = True,
    description = "Use a custom antenna pattern"
    )
        
# transmitter properties panel
class transmitterPropertiesPanel(bpy.types.Panel):
    bl_label = "Transmitter Properties"
    bl_idname = "cloudrf.transmitter_properties_panel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == "EMPTY" and "Transmitter" in obj.name
    
    def draw(self, context):
        layout = self.layout
        obj = context.object
        transmitter_props = obj.transmitter_properties
        
        layout.prop(transmitter_props, "frq")
        layout.prop(transmitter_props, "txw")
        # layout.prop(transmitter_props, "txl")

class transmitterAntennaPropertiesPanel(bpy.types.Panel):
    bl_label = "Antenna Properties"
    bl_idname = "cloudrf.antenna_properties_panel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == "EMPTY" and "Transmitter" in obj.name
    
    def draw(self, context):
        layout = self.layout
        obj = context.object
        transmitter_props = obj.transmitter_properties

        
        layout.prop(transmitter_props, "ant_custom")

        if(transmitter_props.ant_custom):
            layout.prop(transmitter_props, "hbw")
            layout.prop(transmitter_props, "vbw")
            layout.prop(transmitter_props, "fbr")
        else:
            layout.prop(transmitter_props, "ant")
        
        layout.prop(transmitter_props, "txg")


# when the plugin is loaded
# register all classes
def register():
    global loaded_at, plugin_version
    loaded_at = time.strftime("%H:%M:%S")
    plugin_version = manifest_version()

    load_user_templates()

    for cls in MATERIAL_CLASSES:
        bpy.utils.register_class(cls)
    bpy.utils.register_class(properties)
    bpy.utils.register_class(transmitterProperties)
    bpy.utils.register_class(collectionIgnoreProperties)

    bpy.utils.register_class(uploadOperator)
    bpy.utils.register_class(simulateOperator)
    bpy.utils.register_class(simulationReportOperator)
    bpy.utils.register_class(importOperator)
    
    bpy.utils.register_class(transmitterPropertiesPanel)
    bpy.utils.register_class(transmitterAntennaPropertiesPanel)
    
    bpy.utils.register_class(addTransmitterFromTemplateOperator)
    bpy.utils.register_class(applyTemplateToSelectedOperator)
    
    bpy.types.Collection.ignore_properties = bpy.props.PointerProperty(type = collectionIgnoreProperties)

    bpy.types.Scene.props = bpy.props.PointerProperty(type = properties)
    bpy.types.Scene.cloudrf_materials = bpy.props.CollectionProperty(type = materialEntry)
    bpy.types.Scene.cloudrf_materials_index = bpy.props.IntProperty()
    if seed_materials_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(seed_materials_on_load)
    bpy.app.timers.register(seed_materials_timer, first_interval = 0.1)
    bpy.types.Object.transmitter_properties = bpy.props.PointerProperty(type = transmitterProperties)
    
    bpy.utils.register_class(MainPanel)
    bpy.utils.register_class(SettingsPanel)
    bpy.utils.register_class(CLOUDRF_PT_materials)
    bpy.utils.register_class(IOPanel)
    bpy.utils.register_class(browseOperator)


# when the plugin is unloaded (blender is exited)
# unregister all classes
def unregister():
    bpy.utils.unregister_class(properties)
    bpy.utils.unregister_class(transmitterProperties)
    bpy.utils.unregister_class(collectionIgnoreProperties)
    
    bpy.utils.unregister_class(uploadOperator)
    bpy.utils.unregister_class(simulateOperator)
    bpy.utils.unregister_class(simulationReportOperator)
    bpy.utils.unregister_class(importOperator)
    
    bpy.utils.unregister_class(transmitterPropertiesPanel)
    bpy.utils.unregister_class(transmitterAntennaPropertiesPanel)
    
    bpy.utils.unregister_class(addTransmitterFromTemplateOperator)
    bpy.utils.unregister_class(applyTemplateToSelectedOperator)
    
    del bpy.types.Scene.props
    del bpy.types.Scene.cloudrf_materials
    del bpy.types.Scene.cloudrf_materials_index
    if seed_materials_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(seed_materials_on_load)
    bpy.utils.unregister_class(CLOUDRF_PT_materials)
    for cls in reversed(MATERIAL_CLASSES):
        bpy.utils.unregister_class(cls)
    
    bpy.utils.unregister_class(MainPanel)
    bpy.utils.unregister_class(SettingsPanel)
    bpy.utils.unregister_class(IOPanel)
    bpy.utils.unregister_class(browseOperator)


# start
if __name__ == "__main__":
    register()
