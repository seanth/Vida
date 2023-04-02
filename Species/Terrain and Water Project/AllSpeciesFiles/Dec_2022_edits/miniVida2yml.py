
import argparse
import xlrd
import time
import datetime
import os


def get_cli():
    parser = argparse.ArgumentParser(description='Convert miniVida.xls into a Vida species yml file')
    parser.add_argument('-i', '--input', dest="inFile", type=str, required=True, help="Input file.")
    parser.add_argument('-o', '--output', dest="outFile", type=str, default='bla.yml', help="Name of output file.")
    #parser.add_argument('-d', '--debug', dest="doDebug", type=bool, defaut='True', help="Toggle debug string printing on/off. Default is False")

    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = get_cli()
    inFileName = args.inFile
    ymlTempFile = open("speciesTemplate.txt", "r")
    ymlTempTxt = ymlTempFile.read()
    ymlTempFile.close()

    theXLS = xlrd.open_workbook(inFileName)
    firstSheet = theXLS.sheet_by_index(0)
    #cell coordinates: column(y), row(x)

    #Woody mass from total mass
    #Ms=B1*Mt^a1
    B1=firstSheet.cell(2,2).value
    A1=firstSheet.cell(3,2).value

    #Canopy mass(young) from woody mass
    #Mlyoung=B2*Ms^a2
    B2=firstSheet.cell(6,2).value
    A2=firstSheet.cell(7,2).value

    #Canopy mass(mature) from woody mass
    #Mlmature=B3*Ms^a3
    B3=firstSheet.cell(10,2).value
    A3=firstSheet.cell(11,2).value

    #Woody diameter from woody mass
    #Ds=B4*Ms^a4
    B4=firstSheet.cell(14,2).value
    A4=firstSheet.cell(15,2).value

    #Tree height(young) from woody diameter
    #Hsyoung=(B5*Ds^a5)-B6
    B5=firstSheet.cell(18,2).value
    A5=firstSheet.cell(19,2).value
    B6=firstSheet.cell(20,2).value

    #Tree height(mature) from woody diameter
    #Hsmature=B7 + B8 ln Ds
    B7=firstSheet.cell(23,2).value
    B8=firstSheet.cell(24,2).value

    #Total growth from projected area and canopy mass
    #Gt=Alprojected*[B9*(Ml^a6)]
    photoConstant = firstSheet.cell(27,2).value
    photoExponent = firstSheet.cell(28,2).value

    #Seed mass
    idealSeedMass = firstSheet.cell(30,2).value
    fractionCarbonToSeeds = firstSheet.cell(31,2).value
    reproductionConstant = firstSheet.cell(32,2).value
    reproductionExponent = firstSheet.cell(33,2).value
    seedMassMax = firstSheet.cell(34,2).value
    fractionSeedMassToPlant = firstSheet.cell(35,2).value
    fractionCarbonToStem = firstSheet.cell(43,2).value

    #DensityLeaf:
    densityLeaf = firstSheet.cell(37,2).value

    #DensityStem:
    densityStem = firstSheet.cell(38,2).value

    #DensitySeed:
    densitySeed = firstSheet.cell(39,2).value

    #YoungsModStem:
    youngsModulusStem = firstSheet.cell(40,2).value

    #HeightLeaf:
    heightLeaf = firstSheet.cell(41,2).value

    #############
    #waterlogging:
    waterloggingTol = firstSheet.cell(45,2).value

    #drought tolerance:
    droughtTol = firstSheet.cell(46,2).value



    theYear = datetime.date.today().year
    theMonth = '%02d' % datetime.date.today().month #makes sure two digits
    theDay = '%02d' % datetime.date.today().day #makes sure two digits
    theCreationDate = "%d-%s%s" % (theYear, theMonth,theDay)

    theBaseName = os.path.basename(inFileName)
    shortBaseName = os.path.splitext(os.path.basename(inFileName))[0]
    scriptName = os.path.basename(__file__)


    ymlTempTxt = ymlTempTxt % (shortBaseName, scriptName, theBaseName, theCreationDate, 
        densityStem, densityLeaf, densitySeed, heightLeaf, B7, youngsModulusStem, 
        seedMassMax, 
        fractionSeedMassToPlant, fractionCarbonToStem,
        photoConstant, photoExponent,
        fractionCarbonToSeeds, reproductionConstant, reproductionExponent,
        B1, A1, B2, A2, B3, A3, B4, A4, B6, B5, A5, B8, 
        waterloggingTol, droughtTol)
    #print(ymlTempTxt)

    theOutFile = open(args.outFile, "w")
    theOutFile.write(ymlTempTxt)
    theOutFile.close()

    print ("\nFile '%s' created" % args.outFile)
