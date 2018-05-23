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
        self.tools = [Atlantic_Canopy_Extractor, Atlantic_Canopy_Classifier]


class Atlantic_Canopy_Extractor(object):
    def __init__(self):
        self.label = "Step 1 - Atlantic Canopy Extractor"
        self.description = "This tool will extract canopies"
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
        spectral_detail.value = 20
        spatial_detail = arcpy.Parameter(displayName="Spatial Detail", name="spatial_detail", datatype="GPLong",
                                         parameterType="Required", direction="Input", category="Segment Mean Shift Parameters")
      # setting default value
        spatial_detail.value = 20
        min_segment_size = arcpy.Parameter(displayName="Min Segment Size", name="min_segment_size", datatype="GPLong",
                                           parameterType="Required", direction="Input", category="Segment Mean Shift Parameters")
      # setting default value
        min_segment_size.value = 10


        binningmethod = arcpy.Parameter(
            displayName="Binning Method : BINNING <cell_assignment_type> <void_fill_method>",
            name="binningmethod",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="LAS Dataset To Raster Parameters"
        )
        binningmethod.value = "BINNING MAXIMUM NONE"
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

        parameters = [lasfolder, demfile, airphoto, outputdir,  spectral_detail, spatial_detail, min_segment_size, lidarvalue, binningmethod, rasterouttype, samplingtype, samplingvalue]
        return parameters

    def execute(self, parameters, messages):
        environments=arcpy.ListEnvironments()
        for environment in environments:
                arcpy.AddMessage("{0:<30}: {1}".format(environment, arcpy.env[environment]))
        arcpy.AddMessage("Checkout the Spatial extension.")
        arcpy.CheckOutExtension('Spatial')
        #env.pace = arcpy.env.scratchFolder
        lasfolder = parameters[0].valueAsText
        demfile = parameters[1].valueAsText
        ndviinput = parameters[2].valueAsText
        outfolder = parameters[3].valueAsText
        spectral_detail = parameters[4].valueAsText
        spatial_detail = parameters[5].valueAsText
        min_segment_size = parameters[6].valueAsText
        lidarval = parameters[7].valueAsText
        binningmethod = parameters[8].valueAsText
        data_type = parameters[9].valueAsText
        sampling_type = parameters[10].valueAsText
        sampling_value = parameters[11].valueAsText
        fulloutfolder = os.path.join(
            outfolder, timestamp.strftime('%Y%m%d%H%M%S'))
        CompositeList = ""
        arcpy.AddMessage("Creating output folder")
        os.mkdir(fulloutfolder)

        if os.path.exists(os.path.join(lasfolder, "atlantic.lasd")):
           newname=os.path.join(lasfolder,"atlantic.lasd."+timestamp.strftime('%Y%m%d%H%M%S'))
           arcpy.AddMessage("Renaming atlantic.lasd to "+ newname)
           os.rename(os.path.join(lasfolder, "atlantic.lasd"),newname)
        arcpy.AddMessage("Define LAS dataset referencing the current working las file.")
        arcpy.CreateLasDataset_management(lasfolder, os.path.join(lasfolder, "atlantic.lasd"), create_las_prj="NO_FILES")
        CanopyList = ""
        for x in range(1, 6):

            lasLyr = arcpy.CreateUniqueName("Atlantic"+str(x))
            arcpy.management.MakeLasDatasetLayer(os.path.join(lasfolder, "atlantic.lasd"), lasLyr, class_code=1, return_values=str(x))
            outimg = os.path.join(fulloutfolder, "r"+str(x)+".img")
            arcpy.AddMessage(
                "Convert the LAS dataset to a raster for return " + str(x) + ".")
            arcpy.conversion.LasDatasetToRaster(
                lasLyr, outimg, lidarval, binningmethod, data_type, sampling_type, sampling_value, 1)
            outSetNull = SetNull(outimg, outimg, "VALUE <= 0")
            arcpy.AddMessage(
                "Saving "+os.path.join(fulloutfolder, "return"+str(x)+".img"))
            arcpy.CopyRaster_management(outSetNull, os.path.join(
                fulloutfolder, "return"+str(x)+".img"), "DEFAULTS", "", "", "", "", "8_BIT_UNSIGNED")
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
            rout = os.path.join(fulloutfolder, "r"+str(x)+"canopy.img")
            CanopyList = CanopyList+rout+";"
            arcpy.CopyRaster_management(
                outSetNull, rout, "DEFAULTS", "", "", "", "", "8_BIT_UNSIGNED")

        arcpy.AddMessage(
            "Segment Mean Shift phase.")
        seg_raster = SegmentMeanShift(
            os.path.join(
                fulloutfolder, "r1canopy.img"), spectral_detail, spatial_detail,  min_segment_size)
        arcpy.CopyRaster_management(seg_raster, os.path.join(
            fulloutfolder,  "isobj.img"), "DEFAULTS", "", "", "", "", "8_BIT_UNSIGNED")
        outPolygons = os.path.join(fulloutfolder, "Polygons.shp")
        arcpy.RasterToPolygon_conversion(
            os.path.join(
                fulloutfolder, "isobj.img"), outPolygons, "NO_SIMPLIFY")
        outZonalStats = ZonalStatistics(
            outPolygons, "ID", os.path.join(
                fulloutfolder, "r1canopy.img"), "MEAN", "NODATA")
        canpyht = os.path.join(fulloutfolder,  "canpyht.img")
        arcpy.CopyRaster_management(
            outZonalStats, canpyht, "DEFAULTS", "", "", "", "", "8_BIT_UNSIGNED")

        arcpy.env.workspace = ndviinput
        bands = [os.path.join(ndviinput, b)
                 for b in arcpy.ListRasters()]
        #arcpy.AddMessage(bands)

        CompositeList = ndviinput+";"

       
        env.workspace = arcpy.GetSystemEnvironment("TEMP")
        NIR = bands[3]
        Red = bands[0]
        Blue = bands[2]
        NIR_out = "NIR.img"
        Red_out = "Red.img"
        Blue_out = "Blue.img"
        ndviredout=os.path.join(fulloutfolder, "NDVI-red.img")
        ndviblueout=os.path.join(fulloutfolder, "NDVI-blue.img")
        arcpy.CopyRaster_management(NIR, NIR_out)
        arcpy.CopyRaster_management(Red, Red_out)
        arcpy.CopyRaster_management(Blue, Blue_out)
        # Red
        Num = arcpy.sa.Float(Raster(NIR_out) - Raster(Red_out))
        Denom = arcpy.sa.Float(Raster(NIR_out) + Raster(Red_out))
        NIR_eq = arcpy.sa.Divide(Num, Denom)
        NIR_eq2 = (NIR_eq+1)*100
        NIR_eq2.save(ndviredout)
        
        
        # Blue
        Num = arcpy.sa.Float(Raster(NIR_out) - Raster(Blue_out))
        Denom = arcpy.sa.Float(Raster(NIR_out) + Raster(Blue_out))
        NIR_eq = arcpy.sa.Divide(Num, Denom)
        NIR_eq2 = (NIR_eq+1)*100
        NIR_eq2.save(ndviblueout)

        #Cleanup    
        arcpy.Delete_management(NIR_out)
        arcpy.Delete_management(Red_out)
        arcpy.Delete_management(Blue_out)
        arcpy.ResetEnvironments()
        CompositeList = CompositeList+ndviredout+";"
        CompositeList = CompositeList+ndviblueout+";"
        CompositeList = CompositeList+CanopyList

        arcpy.env.extent = "MINOF"
        arcpy.AddMessage("Create composite image.")
        arcpy.AddMessage("CompositeList:")
        arcpy.AddMessage(CompositeList)
        compbands = os.path.join(fulloutfolder, "compbands.img")
        arcpy.CompositeBands_management(CompositeList, compbands)
        # stratify according to the height

        arcpy.ResetEnvironments()
        arcpy.AddMessage("stratify composite image according to the height")
        # gte15=os.path.join(fulloutfolder, "compbandsgte15ft.img")
        # v6and15=os.path.join(fulloutfolder, "compbandsgte6andlt15ft.img")
        # v1and6=os.path.join(fulloutfolder, "compbandsgte1andlt6ft.img")
        # gt1=os.path.join(fulloutfolder, "compbandslt1ft.img")
        # arcpy.gp.SetNull_sa(canpyht, compbands, gte15, "\"Value\" <=15")
        # arcpy.gp.SetNull_sa(canpyht, compbands, v6and15, "\"Value\" <=6 OR \"Value\" > 15")
        # arcpy.gp.SetNull_sa(canpyht, compbands, v1and6, "\"Value\" <=1 OR \"Value\" > 6")
        # arcpy.gp.SetNull_sa(canpyht, compbands, gt1, "\"Value\" >1")


        Outsetnull = SetNull(canpyht, canpyht, "VALUE <= 15")
        # Outsetnull.save(os.path.join(fulloutfolder, "mask1.img"))
        maskfile = os.path.join(fulloutfolder, "mask1.img")
        arcpy.CopyRaster_management(
            Outsetnull, maskfile, "", "", "0", "", "", "8_BIT_UNSIGNED","")
        outExtractByMask = ExtractByMask(compbands, maskfile)
        outExtractByMask.save(os.path.join(
            fulloutfolder, "compbandsgte15ft.img"))

        Outsetnull = SetNull(canpyht, canpyht, "VALUE <= 6 OR VALUE > 15")
        # Outsetnull.save(os.path.join(fulloutfolder, "mask2.img"))
        maskfile = os.path.join(fulloutfolder, "mask2.img")
        arcpy.CopyRaster_management(
            Outsetnull, maskfile, "", "", "0", "", "", "8_BIT_UNSIGNED","")
        outExtractByMask = ExtractByMask(compbands, maskfile)
        outExtractByMask.save(os.path.join(
            fulloutfolder, "compbandsgte6andlt15ft.img"))

        Outsetnull = SetNull(canpyht, canpyht, "VALUE <= 1 OR VALUE > 6")
        maskfile = os.path.join(fulloutfolder, "mask3.img")
        arcpy.CopyRaster_management(
            Outsetnull, maskfile, "", "", "0", "", "", "8_BIT_UNSIGNED","")
        outExtractByMask = ExtractByMask(compbands, maskfile)
        outExtractByMask.save(os.path.join(
            fulloutfolder, "compbandsgte1andlt6ft.img"))

        Outsetnull = SetNull(canpyht, canpyht, "VALUE > 1")
        maskfile = os.path.join(fulloutfolder, "mask4.img")
        arcpy.CopyRaster_management(
            Outsetnull, maskfile, "", "", "0", "", "", "8_BIT_UNSIGNED","")
        outExtractByMask = ExtractByMask(compbands, maskfile)
        outExtractByMask.save(os.path.join(
fulloutfolder, "compbandslt1ft.img"))

        arcpy.AddMessage("Finished!")
        return
class Atlantic_Canopy_Classifier(object):
    def __init__(self):
        self.label = "Step 2 - Atlantic Canopy Classifier"
        self.description = "This tool will Classify Canopies"
        self.canRunInBackground = False

    def getParameterInfo(self):
        canopyfile = arcpy.Parameter(displayName="Stratified Canopy Image", name="canopyfile",
                                     datatype="DEFile", parameterType="Required", direction="Input")
        straining_sites = arcpy.Parameter(displayName="Training Sites Shapefile", name="straining_sites",
                                          datatype="DEFile", parameterType="Required", direction="Input")
        parameters = [canopyfile, straining_sites]
        return parameters

    def execute(self, parameters, messages):
        # env.workspace = arcpy.env.scratchFolder
        canopyfile = parameters[0].valueAsText
        straining_sites = parameters[1].valueAsText

        outfolder = os.path.dirname(os.path.abspath(canopyfile))
        outecd = os.path.join(outfolder, os.path.splitext(
            os.path.basename(canopyfile))[0]+'.ecd')
        TrainRandomTreesClassifier(
            canopyfile, straining_sites, outecd, "", "50", "30", "1000", "COLOR;MEAN")
        classimg = ClassifyRaster(canopyfile, outecd)
        classimg.save(os.path.join(outfolder, os.path.splitext(
            os.path.basename(canopyfile))[0]+'_class.img'))
        arcpy.AddMessage(outecd)