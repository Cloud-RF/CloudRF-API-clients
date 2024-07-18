import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, IntProperty, FloatProperty, EnumProperty
from multiprocessing import Pool
import mathutils
import os
import json
import requests
import time

# plugin info
bl_info = {
    "name": "CloudRF 3D",
    "description": "Simulate RF propagation using the CloudRF 3D API",
    "author": "CloudRF.com",
    "version": (1, 0, 1),
    "blender": (3, 6, 0),
    "category": "Import-Export"
}

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


def addTransmitter(data):
    bpy.ops.object.empty_add(location = (0, 0, 0))
    
    obj = bpy.context.active_object
    obj.name = "Transmitter"
    
    transmitter_props = obj.transmitter_properties
    if not transmitter_props:
        transmitter_props = obj.transmitter_properties = bpy.props.PointerProperty(type = transmitterProperties)

    obj.transmitter_properties.frq = data["frq"]
    obj.transmitter_properties.txw = data["txw"]
    obj.transmitter_properties.ant = data["antenna"]["ant"]
    obj.transmitter_properties.ant_custom = data["antenna"]["ant"] == 0
    obj.transmitter_properties.hbw = data["antenna"]["hbw"]
    obj.transmitter_properties.vbw = data["antenna"]["vbw"]
    obj.transmitter_properties.txg = data["antenna"]["txg"]
    obj.transmitter_properties.txl = data["antenna"]["txl"]
    obj.transmitter_properties.fbr = data["antenna"]["fbr"]

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
    bl_label = "Add Transmitter"
    bl_idname = "cloudrf.add_transmitter_template_add"

    action: bpy.props.EnumProperty(name="cloudrf.templates", items=templates_to_enum)

    def execute(self, context):
        template_name = self.properties.action

        if not template_name in templates:
            self.report({"ERROR"}, f"Could not find template with name: {template_name}")
            return {"ERROR"}

        addTransmitter(templates[template_name])

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

                # scene.props.max_reflections = data["3d"]["max_reflections"]
                # scene.props.res = data["output"]["res"]
            
        except FileNotFoundError:
            self.report({"ERROR"}, "File not found please specify a valid file!")
            return {"CANCELLED"}
        except json.JSONDecodeError:
            self.report({"ERROR"}, "Please provide a valid JSON format!")
            return {"CANCELLED"}
        
        self.report({"INFO"}, f"Successfully imported template {name}!\n{templates[name]}")
        
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
                res = requests.post(model_upload_url, headers = key_json, files = {"file": file}, verify = False)
                self.report({"INFO"}, "Response: \n" + str(res.content))
        except:
            self.report({"ERROR"}, "An unexpected error occured!. Ensure the model is saved somewhere that it can be accessed!")
            return {"CANCELLED"}

        return {"FINISHED"}


# simulate button
class simulateOperator(bpy.types.Operator):
    
    # settings for the button
    bl_idname = "cloudrf.simulate"
    bl_label = "Simulate"
    
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
        calculate_url = scene.props.server_address + "/3d"
        file_url = ""
        
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

        try:
            
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

                    transmitter_data = {
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
                    }
                
                    transmitters.append(transmitter_data)
        
            # request settings for API
            request_options = {
                "transmitters": transmitters,
                "3d": {
                    "input_file": "crf_blender_plugin_model.glb",
                    "max_reflections": scene.props.max_reflections
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
            self.report({"INFO"}, "Request: \n" + str(request_options))
            
            # make request
            response = requests.post(json = request_options, headers = key_json, url = calculate_url, timeout=120, verify = False)
            json = response.json() # get json from response
            self.report({"INFO"}, "Response: \n" + str(response.content))
            last_calc_time = float(json["elapsed_s"]) 
            file_url = json["model_file"] # find the url to the glb file result
        except: # for example no API key
            
            self.report({"ERROR"}, "An unexpected error occured!")
            return {"CANCELLED"}
        
        try:
            response = requests.get(file_url, headers = key_json, verify = False) # make request to URL with file
            response.raise_for_status()
        except:
            self.report({"INFO"}, "Response: \n" + str(response.content))
            self.report({"ERROR"}, "An unexpected error occured!")
            return {"CANCELLED"}
        
        
        # declare location for file to be saved
        file_path = bpy.data.filepath + "result.glb"

        # save the downloaded glb file
        with open(file_path, "wb") as file:
            file.write(response.content)

        if not os.path.exists(file_path): # for example invalid permissions
            self.report({"ERROR"}, "There was an unexpected error saving the result!")
            return {"CANCELLED"}

        old_objs = set(context.scene.objects)

        # import the downloaded glb file into the current scene
        bpy.ops.import_scene.gltf(filepath = file_path)

        imported_objs = set(context.scene.objects) - old_objs

        collection_name = f"cloudRF 3D Result {time.time()}"
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
        collection.ignore_properties.ignore = True
        for obj in imported_objs:
            for coll in obj.users_collection:
                coll.objects.unlink(obj)
            collection.objects.link(obj)

        self.report({"INFO"}, ("Simulation success! In " + str(last_calc_time) + " seconds"))

        return {"FINISHED"}

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
        
        # draw all options in cloud rf panel
        l.operator(uploadOperator.bl_idname)
        l.operator(simulateOperator.bl_idname)
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


class transmitterAdds(bpy.types.Menu):
    bl_label = "Transmitters"
    bl_idname = "cloudrf.transmitter_adds"
    
    def draw(self, context):
        layout = self.layout
        
        layout.operator_enum(addTransmitterFromTemplateOperator.bl_idname, "action")

        for template in templates:
            pass

# add the transmitter object to the add panel
def menu_function(self, context):
    self.layout.menu(transmitterAdds.bl_idname)

# when the plugin is loaded
# register all classes
def register():
    bpy.utils.register_class(properties)
    bpy.utils.register_class(transmitterProperties)
    bpy.utils.register_class(collectionIgnoreProperties)

    bpy.utils.register_class(uploadOperator)
    bpy.utils.register_class(simulateOperator)
    bpy.utils.register_class(importOperator)
    
    bpy.utils.register_class(transmitterPropertiesPanel)
    bpy.utils.register_class(transmitterAntennaPropertiesPanel)
    
    bpy.utils.register_class(addTransmitterFromTemplateOperator)
    
    bpy.utils.register_class(transmitterAdds)
    
    bpy.types.Collection.ignore_properties = bpy.props.PointerProperty(type = collectionIgnoreProperties)

    bpy.types.Scene.props = bpy.props.PointerProperty(type = properties)
    bpy.types.Object.transmitter_properties = bpy.props.PointerProperty(type = transmitterProperties)
    
    bpy.utils.register_class(MainPanel)
    bpy.utils.register_class(SettingsPanel)
    bpy.utils.register_class(IOPanel)
    bpy.utils.register_class(browseOperator)
    
    bpy.types.VIEW3D_MT_add.append(menu_function)

# when the plugin is unloaded (blender is exited)
# unregister all classes
def unregister():
    bpy.utils.unregister_class(properties)
    bpy.utils.unregister_class(transmitterProperties)
    bpy.utils.unregister_class(collectionIgnoreProperties)
    
    bpy.utils.unregister_class(uploadOperator)
    bpy.utils.unregister_class(simulateOperator)
    bpy.utils.unregister_class(importOperator)
    
    bpy.utils.unregister_class(transmitterPropertiesPanel)
    bpy.utils.unregister_class(transmitterAntennaPropertiesPanel)
    
    bpy.utils.unregister_class(addTransmitterFromTemplateOperator)
    
    bpy.utils.unregister_class(transmitterAdds)
    
    del bpy.types.Scene.props
    
    bpy.utils.unregister_class(MainPanel)
    bpy.utils.unregister_class(SettingsPanel)
    bpy.utils.unregister_class(IOPanel)
    bpy.utils.unregister_class(browseOperator)
    
    bpy.types.VIEW3D_MT_add.remove(menu_function)

# start
if __name__ == "__main__":
    register()
