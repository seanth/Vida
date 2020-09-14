import pandas

theFile = "rastert_emidala1_TableToExcel.xlsx"

theData = pandas.read_excel(theFile, skiprows=7)

allMaxForEachColumn = theData.max()
absMax = allMaxForEachColumn.max()

print absMax

allMinForEachColumn = theData.min()
absMin = allMinForEachColumn.min()

print absMin
