import arcpy
import string
import os
import datetime
from arcpy import env
from time import sleep
from arcpy.sa import *


timestamp = datetime.datetime.now()


class Toolbox(object):
    def __init__(self):
        self.label = "Atlantic Toolbox"
        self.alias = "Atlantic ArcGIS Toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [Atlantic_Canopy_Classifier]


class Atlantic_Canopy_Classifier(object):
    def __init__(self):
        self.label = "Atlantic_Canopy_Classifier"
        self.description = "This tool will Classify Canopies"
        self.canRunInBackground = False

    def getParameterInfo(self):

     # Input parameters
        lasfolder = arcpy.Parameter(displayName="LAS Dataset Folder", name="lasdir",
                                    datatype="DEFolder", parameterType="Required", direction="Input")
        demfile = arcpy.Parameter(displayName="DEM  Input File", name="demdir",
                                  datatype="DEFile", parameterType="Required", direction="Input")
        airphoto = arcpy.Parameter(displayName="Aerial photo ", name="airphoto2",
                                  datatype="DEFile", parameterType="Required", direction="Input")
        outputdir = arcpy.Parameter(displayName="Output Directory", name="outputdir",
                                    datatype="DEFolder", parameterType="Required", direction="Input")

        spectral_detail = arcpy.Parameter(displayName="Spectral Detail", name="spectral_detail", datatype="GPDouble",
                                          parameterType="Required", direction="Input", category="Segment Mean Shift Parameters")
      # setting default value
        spectral_detail.value = 15.5
        spatial_detail = arcpy.Parameter(displayName="Spatial Detail", name="spatial_detail", datatype="GPLong",
                                         parameterType="Required", direction="Input", category="Segment Mean Shift Parameters")
      # setting default value
        spatial_detail.value = 15
        min_segment_size = arcpy.Parameter(displayName="Min Segment Size", name="min_segment_size", datatype="GPLong",
                                           parameterType="Required", direction="Input", category="Segment Mean Shift Parameters")
      # setting default value
        min_segment_size.value = 10
        height = arcpy.Parameter(displayName="Any value less than or equal to this will be converted to 0", name="height",
                                 datatype="GPDouble", parameterType="Required", direction="Input", category="Convert Height Parameters")
      # setting default value
        height.value = 2.0

        binningmethod = arcpy.Parameter(
            displayName="Binning Method : BINNING <cell_assignment_type> <void_fill_method>",
            name="binningmethod",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="LAS Dataset To Raster Parameters"
        )
        binningmethod.value = "BINNING MINIMUM NONE"
        binningmethod.filter.type = "ValueList"
        binningmethod.filter.list = ["BINNING AVERAGE NONE", "BINNING AVERAGE SIMPLE", "BINNING AVERAGE LINEAR", "BINNING AVERAGE NATURAL_NEIGHBOR", "BINNING MINIMUM NONE", "BINNING MINIMUM SIMPLE", "BINNING MINIMUM LINEAR", "BINNING MINIMUM NATURAL_NEIGHBOR", "BINNING MAXIMUM NONE",
                                     "BINNING MAXIMUM SIMPLE", "BINNING MAXIMUM LINEAR", "BINNING MAXIMUM NATURAL_NEIGHBOR", "BINNING IDW NONE", "BINNING IDW SIMPLE", "BINNING IDW LINEAR", "BINNING IDW NATURAL_NEIGHBOR", "BINNING NEAREST NONE", "BINNING NEAREST SIMPLE", "BINNING NEAREST LINEAR", "BINNING NEAREST NATURAL_NEIGHBOR"]

        lidarvalue = arcpy.Parameter(
            displayName="The lidar data that will be used to generate the raster output.",
            name="lidarvalue",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="LAS Dataset To Raster Parameters"
        )
        lidarvalue.value = "ELEVATION"

        lidarvalue.filter.type = "ValueList"
        lidarvalue.filter.list = ["ELEVATION", "INTENSITY"]

        rasterouttype = arcpy.Parameter(
            displayName="The raster output value type.",
            name="rasterouttype",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="LAS Dataset To Raster Parameters"
        )
        rasterouttype.value = "FLOAT"

        rasterouttype.filter.type = "ValueList"
        rasterouttype.filter.list = ["INT", "FLOAT"]

        samplingtype = arcpy.Parameter(
            displayName="method used for interpreting the Sampling Value",
            name="samplingtype",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="LAS Dataset To Raster Parameters"
        )
        samplingtype.value = "CELLSIZE"

        samplingtype.filter.type = "ValueList"
        samplingtype.filter.list = ["OBSERVATIONS", "CELLSIZE"]

        samplingvalue = arcpy.Parameter(displayName="samplingvalue", name="samplingvalue", datatype="GPDouble",
                                        parameterType="Required", direction="Input", category="LAS Dataset To Raster Parameters")
        samplingvalue.value = 2

        parameters = [lasfolder, demfile, airphoto, outputdir,  spectral_detail, spatial_detail, min_segment_size,
                      height, lidarvalue, binningmethod, rasterouttype, samplingtype, samplingvalue]
        return parameters

    def isLicensed(self):  # optional
        return True

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        arcpy.AddMessage("Checkout the Spatial extension.")
        arcpy.CheckOutExtension('Spatial')
       # arcpy.SetProgressor("default", "Working...", 0, 2, 1)
        env.workspace = arcpy.env.scratchFolder
        lasfolder = parameters[0].valueAsText
        demfile = parameters[1].valueAsText
        ndviinput = parameters[2].valueAsText
        outfolder = parameters[3].valueAsText
        spectral_detail = parameters[4].valueAsText
        spatial_detail = parameters[5].valueAsText
        min_segment_size = parameters[6].valueAsText
       # band_indexes = ""
      #  height = parameters[7].valueAsText
        lidarval = parameters[8].valueAsText
        binningmethod = parameters[9].valueAsText
        data_type = parameters[10].valueAsText
        sampling_type = parameters[11].valueAsText
        sampling_value = parameters[12].valueAsText
        fulloutfolder = os.path.join(
            outfolder, timestamp.strftime('%Y%m%d%H%M%S'))
        CompositeList = ""
        arcpy.AddMessage("Creating output folder")
        os.mkdir(fulloutfolder)

        if not os.path.exists(os.path.join(lasfolder, "Atlantic_Canopy_Classifier.lasd")):
            arcpy.AddMessage(
                "Define LAS dataset referencing the current working las file.")
            arcpy.CreateLasDataset_management(lasfolder, os.path.join(
                lasfolder, "Atlantic_Canopy_Classifier.lasd"), create_las_prj="NO_FILES")
        CanopyList=""
        for x in range(1, 6):

            #arcpy.AddMessage("Creating output file variable")
            # outputfile = os.path.join(fulloutfolder, "r"+str(x)+".tif")
            #arcpy.AddMessage("Create a unique name in the specified workspace")
            lasLyr = arcpy.CreateUniqueName(str(x))
            #arcpy.AddMessage("Create a LAS dataset layer that can apply filters to our LAS points")
            arcpy.management.MakeLasDatasetLayer(os.path.join(lasfolder, "atlantic.lasd"), lasLyr, class_code=1, return_values=str(x))
            #arcpy.AddMessage("Create variable for output image location.")
            outimg = os.path.join(fulloutfolder, "r"+str(x)+".img")
            arcpy.AddMessage("Convert the LAS dataset to a raster for return " +str(x)+ ".")
            arcpy.conversion.LasDatasetToRaster(
                lasLyr, outimg, lidarval, binningmethod, data_type, sampling_type, sampling_value, 1)
            outSetNull = SetNull(outimg, outimg, "VALUE <= 0")
            arcpy.AddMessage("Saving "+os.path.join(fulloutfolder, "return"+str(x)+".img"))
            arcpy.CopyRaster_management(outSetNull,os.path.join(fulloutfolder, "return"+str(x)+".img"),"DEFAULTS","","","","","8_BIT_UNSIGNED")
            # outSetNull.save(os.path.join(
            #     fulloutfolder, "return"+str(x)+".img"))
            arcpy.AddMessage("Checkout the Spatial extension.")
            arcpy.CheckOutExtension('Spatial')
            arcpy.AddMessage(
                "Subtract the dem data from the raster we created from the LAS")
            outMinus = Raster(outimg) - Raster(demfile)
            arcpy.AddMessage(
                "Set any value that is less than or equal to 0 to Null")
            outSetNull = SetNull(outMinus, outMinus, "VALUE <= 0")
            arcpy.AddMessage(
                "Save the image that has newly converted Null values")
            # outSetNull
            #CompositeList = CompositeList + \
            #    os.path.join(fulloutfolder, "r"+str(x)+"canopy.img; ")
            rout=os.path.join(fulloutfolder, "r"+str(x)+"canopy.img")
            CanopyList=CanopyList+rout+";"
            arcpy.CopyRaster_management(outSetNull,rout,"DEFAULTS","","","","","8_BIT_UNSIGNED")
            # outSetNull.save(os.path.join(
            #     fulloutfolder, "r"+str(x)+"canopy.img"))
                
        arcpy.AddMessage(
            "Segment Mean Shift phase. This will take some time. Be patient.")
        seg_raster = SegmentMeanShift(
            os.path.join(
                fulloutfolder, "r1canopy.img"), spectral_detail, spatial_detail,  min_segment_size)
        arcpy.AddMessage("1")
        arcpy.CopyRaster_management(seg_raster,os.path.join(fulloutfolder,  "isobj.img"),"DEFAULTS","","","","","8_BIT_UNSIGNED")
        arcpy.AddMessage("2")

        # seg_raster.save(os.path.join(
        #     fulloutfolder, "isobj.img"))
        outPolygons = os.path.join(fulloutfolder, "Polygons.shp")
        arcpy.AddMessage("3")
      #  field = "VALUE"
        arcpy.RasterToPolygon_conversion(
            os.path.join(
                fulloutfolder, "isobj.img"), outPolygons, "NO_SIMPLIFY")
        arcpy.AddMessage("4")
        outZonalStats = ZonalStatistics(
            outPolygons, "ID", os.path.join(
                fulloutfolder, "r1canopy.img"), "MEAN", "NODATA")
        arcpy.AddMessage("5")
        # outZonalStats.save(os.path.join(
        #     fulloutfolder, "canpyht.img"))
        arcpy.CopyRaster_management(outZonalStats,os.path.join(fulloutfolder,  "canpyht.img"),"DEFAULTS","","","","","8_BIT_UNSIGNED")
        arcpy.AddMessage("6")
        #ndviinput = airphoto
    #    ndvioutput = os.path.join(fulloutfolder, "NDVI-")
        

        # use the input file as a workspace to get the bands.
        arcpy.env.workspace = ndviinput
        arcpy.AddMessage("7")
        bands = [Raster(os.path.join(ndviinput, b))
                        for b in arcpy.ListRasters()]
        arcpy.AddMessage("8")
        arcpy.AddMessage(bands)
        arcpy.AddMessage("9")
        # for band in bands:
        #     arcpy.AddMessage(band)
        #CompositeList=ndviinput+";"
        #CompositeList = CompositeList+bands[0]+";"+bands[1]+";"+bands[2]+";"+bands[3]+";"
        # switch to default workspace
        # env.workspace = arcpy.env.scratchFolder
        # create and save the ndvi
        # red = ndvioutput+"red-"+ndviinput
        arcpy.AddMessage("a")
        red = os.path.join(fulloutfolder, "NDVI-red.img")
        arcpy.AddMessage("b")
        CompositeList = CompositeList+red+";"
        arcpy.AddMessage("c")
        # ndvioutput+"blue-"+ndviinput
        blue = os.path.join(fulloutfolder, "NDVI-blue.img")
        arcpy.AddMessage("d")
        CompositeList = CompositeList+blue+";"
        arcpy.AddMessage("e")
        CompositeList = CompositeList+CanopyList
        arcpy.AddMessage("f")
        arcpy.AddMessage(CompositeList)
        arcpy.AddMessage("g")
        arcpy.AddMessage("Generate red band ndvi")
        ndvired = ((((Float(bands[3]) - Float(bands[0])) /
                   (Float(bands[3]) + Float(bands[0])))+1)*100)
        # ndvired.save(red)
        arcpy.AddMessage("h")
        arcpy.CopyRaster_management(ndvired,red,"DEFAULTS","","","","","8_BIT_UNSIGNED")
        arcpy.AddMessage("i")
        arcpy.AddMessage("Generate blue band ndvi")
        ndviblue = (
            (((Float(bands[3]) - Float(bands[2])) / (Float(bands[3]) + Float(bands[2])))+1)*100)
        # ndviblue.save(blue)
        arcpy.AddMessage("j")
        arcpy.CopyRaster_management(ndviblue,blue,"DEFAULTS","","","","","8_BIT_UNSIGNED")
        arcpy.AddMessage("k")
        arcpy.CompositeBands_management(CompositeList, os.path.join(fulloutfolder, "compbands.img"))
        arcpy.AddMessage("Finished!")
        return
