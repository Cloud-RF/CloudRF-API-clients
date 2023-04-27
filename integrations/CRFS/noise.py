#!/usr/bin/env python3
# A class for different noise sources
import ncplib
import matplotlib.pyplot as plt
import numpy as np

class NoiseSource:

    # CRFS RFEye https://python3-ncplib.readthedocs.io
    async def rfeye(IPaddress,frequency,bandwidth,verbose=0):
        startFreq = int(frequency - (bandwidth/2))
        stopFreq = int(frequency + (bandwidth/2))     

        # Convert positive dB value to dBm by subtracting a constant
        def todbm(x):
            return x - 180

        # Connect to the RFEye
        async with await ncplib.connect(IPaddress) as connection:
            response = connection.send("DSPC", "SWEP", FSTA=startFreq, FSTP=stopFreq, INPT=1, BDEX=1, BINP=2)
            field = await response.recv()
            fft = field["PDAT"] # Measurements array
            dBm = np.array(list(map(todbm, fft))) # Convert to dBm
            meanNoise = int(np.mean(dBm)) # Average noise figure. You may want max() if signal is vulnerable

            # Plot the FFT?
            if verbose:
                fig, ax = plt.subplots()
                step = bandwidth / len(fft)
                frequencies = np.arange(startFreq,stopFreq,step)
                ax.plot(frequencies,dBm)
                ax.set_ylabel('dBm')
                ax.set_xlabel('MHz')
                ax.set_title('%d MHz with %d MHz Bandwidth' % (frequency,bandwidth))
                plt.ylim([-120, -10])
                plt.show()

            return meanNoise