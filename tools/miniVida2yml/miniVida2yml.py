
import argparse
import xlrd
import time
import datetime
import os

def get_cli():
    parser = argparse.ArgumentParser(description='Convert miniVida.xls into a Vida species yml file')
    parser.add_argument('-i', '--input', dest="inFile", type=str, required=True, help="Input file.")
    parser.add_argument('-o', '--output', dest="outFile", type=str, default='bla.yml', help="Name of output file.")

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
    # print B1
    # print A1

    #Canopy mass(young) from woody mass
    #Mlyoung=B2*Ms^a2
    B2=firstSheet.cell(6,2).value
    A2=firstSheet.cell(7,2).value
    # print B2
    # print A2


    #Canopy mass(mature) from woody mass
    #Mlmature=B3*Ms^a3
    B3=firstSheet.cell(10,2).value
    A3=firstSheet.cell(11,2).value
    # print B3
    # print A3


    #Woody diameter from woody mass
    #Ds=B4*Ms^a4
    B4=firstSheet.cell(14,2).value
    A4=firstSheet.cell(15,2).value
    # print B4
    # print A4


    #Tree height(young) from woody diameter
    #Hsyoung=(B5*Ds^a5)-B6
    B5=firstSheet.cell(18,2).value
    A5=firstSheet.cell(19,2).value
    B6=firstSheet.cell(20,2).value
    # print B5
    # print A5
    # print B6


    #Tree height(mature) from woody diameter
    #Hsmature=B7 + B8 ln Ds
    B7=firstSheet.cell(23,2).value
    B8=firstSheet.cell(24,2).value
    # print B7
    # print B8


    #Total growth from projected area and canopy mass
    #Gt=Alprojected*[B9*(Ml^a6)]
    B9 = firstSheet.cell(27,2).value
    A6 = firstSheet.cell(28,2).value
    # print B9
    # print A6


    #IdealSeedlingMass
    seedMass = firstSheet.cell(30,2).value
    # print seedMass

    #DensityLeaf:
    densityLeaf = firstSheet.cell(31,2).value
    # print densityLeaf

    #DensityStem:
    densityStem = firstSheet.cell(32,2).value
    # print densityStem

    #YoungsModStem:
    youngsModulusStem = firstSheet.cell(33,2).value
    # print youngsModulusStem

    #HeightLeaf:
    heightLeaf = firstSheet.cell(34,2).value
    # print heightLeaf

    #fractStem@germ:
    fractStem = firstSheet.cell(36,2).value
    # print fractStem

    #waterlogging:
    waterloggingTol = firstSheet.cell(38,2).value
    #print(waterloggingTol)

    #drought tolerance:
    droughtTol = firstSheet.cell(39,2).value
    #print(droughtTol)


    theYear = datetime.date.today().year
    theMonth = '%02d' % datetime.date.today().month #makes sure two digits
    theDay = '%02d' % datetime.date.today().day #makes sure two digits
    theCreationDate = "%d-%s%s" % (theYear, theMonth,theDay)

    theBaseName = os.path.basename(inFileName)
    shortBaseName = os.path.splitext(os.path.basename(inFileName))[0]
    scriptName = os.path.basename(__file__)

    ymlTempTxt = ymlTempTxt % (shortBaseName, scriptName, theBaseName, theCreationDate, densityStem, densityLeaf, densityStem/2.0, heightLeaf, B7, youngsModulusStem, 
    	B9, A6, fractStem, B1, A1, B2, A2, B3, A3, B4, A4, B6, B5, A5, B8, waterloggingTol, droughtTol)
    #print ymlTempTxt

    theOutFile = open(args.outFile, "w")
    theOutFile.write(ymlTempTxt)
    theOutFile.close()

    print ("\nFile '%s' created" % args.outFile)
