import ezdxf
from ezdxf import units

def Cube():
    return [
            [(0,0,0),(1,0,0),(1,0,1),(0,0,1)],
            [(1,0,0),(1,1,0),(1,1,1),(1,0,1)],
            [(1,1,0),(0,1,0),(0,1,1),(1,1,1)],
            [(0,1,0),(0,0,0),(0,0,1),(0,1,1)],
            [(0,0,1),(1,0,1),(1,1,1),(0,1,1)],
            [(0,1,0),(1,1,0),(1,0,0),(0,0,0)]
            ]


doc = ezdxf.new('R2010')
# Set meter as document/modelspace units
doc.units = units.M
# which is a shortcut (including validation) for
#doc.header['$INSUNITS'] = units.M
doc.header['$MEASUREMENT'] = 1 #0==Imperial, 1==Metric

#make the modelspace (msp)
msp = doc.modelspace()
msp.units = doc.units

############################
#Blocks
aBlock = doc.blocks.new(name='THEGARDEN')
theFaceList = Cube()
for x in theFaceList:
	aBlock.add_3dface(x)
theFaceList=""

aBlock = doc.blocks.new(name='SEED')
theFaceList = Cube()
for x in theFaceList:
	aBlock.add_3dface(x)
theFaceList=""

############################
#Now insert a block
msp.add_blockref('THEGARDEN', (0.0, 0.0, 0.0), dxfattribs={
    'xscale': 1.0,
    'yscale': 1.0,
    'zscale': 1.0,
    'rotation': 0.0,
    'color': 0
})

msp.add_blockref('SEED', (2.0, 2.0, 2.0), dxfattribs={
    'xscale': 0.5,
    'yscale': 0.5,
    'zscale': 0.5,
    'rotation': 0.0,
    'color': 0
})

doc.saveas("blockref_tutorial.dxf")

