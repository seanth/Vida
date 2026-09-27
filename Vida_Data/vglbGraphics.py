"""This file is part of Vida.
    --------------------------
    Copyright 2026, Sean T. Hammond

    Vida is experimental in nature and is made available as a research courtesy "AS IS," but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

    You should have received a copy of academic software agreement along with Vida. If not, see <https://github.com/seanth/Vida/blob/master/LICENSE.txt>.
"""

#Writes the garden directly to a binary glTF (.glb) file, without going
#through DXF and assimp.
#
#Scene layout:
#   Vida (root node, rotates Vida's z-up world into glTF's y-up convention)
#     ground            the thin garden slab (same as THEGARDEN in the DXF)
#     terrain           one mesh built from the terrain image (if any)
#     water             a solid or see-through block up to the water level, or nothing (waterStyle)
#     plants
#       <species> <name>   one node per plant, with plant data in "extras"
#         stem
#         canopy
#     seeds
#       seeds_dispersed    all dispersed seeds of one colour merged into one mesh
#       seeds_attached     all attached seeds of one colour merged into one mesh
#
#Colours are taken straight from the plants' HSV values and stored as
#materials (not vertex colours), which is the most widely supported way
#to colour a glTF file.
#STH 2026-0926

import colorsys
import json
import math
import random
import struct

import numpy as np
from PIL import Image

import vterrainImport as terrain_utils
import vdxfGraphics #for the Cube() and Sphere() shape definitions

WATER_STYLES = ("solid", "translucent", "none")

GROUND_RGB = (0.6, 0.6, 0.6)
TERRAIN_RGB = (104/255.0, 78/255.0, 69/255.0) #ACI 27, the colour used in the DXF
WATER_RGB = (0.15, 0.3, 0.9)
WATER_TRANSLUCENT_ALPHA = 0.5

#glTF constants
FLOAT = 5126
UNSIGNED_INT = 5125
ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963


###########################################################################
#colour helpers

def hsvToRGB(theHSV):
    #the input is in the form [H in degrees, S in decimal1, V in decimal1]
    #same convention as colour_utils.HSV_to_ACI()
    return colorsys.hsv_to_rgb((theHSV[0] % 360.0)/360.0, theHSV[1], theHSV[2])

def srgbToLinear(c):
    #glTF baseColorFactor is linear. Convert so viewers show the intended colour
    if c <= 0.04045:
        return c/12.92
    return ((c + 0.055)/1.055)**2.4

###########################################################################
#geometry helpers

def facesToTriangles(theFaceList):
    #Vida's shapes are lists of 4-point 3dfaces. A face whose last two points
    #are the same is a triangle, otherwise it is a quad (two triangles).
    #Returns a list of triangles, and for each triangle the index of the
    #face it came from (so faces can be coloured individually)
    theTriangles = []
    theFaceIndex = []
    for i in range(len(theFaceList)):
        p = theFaceList[i]
        theTriangles.append((p[0], p[1], p[2]))
        theFaceIndex.append(i)
        if tuple(p[3]) != tuple(p[2]):
            theTriangles.append((p[0], p[2], p[3]))
            theFaceIndex.append(i)
    return theTriangles, theFaceIndex

def weldTriangles(theTriangles, theCentre, smooth):
    #build indexed geometry from a triangle list. Triangles are wound so their
    #normals point away from theCentre (the DXF shapes don't have consistent
    #winding). smooth=True shares vertices and averages normals,
    #smooth=False keeps hard edges (used for boxes)
    theCentre = np.array(theCentre, dtype=np.float64)
    positions = []
    normals = []
    indices = []
    lookup = {}
    kept = []
    for t in range(len(theTriangles)):
        tri = theTriangles[t]
        a = np.array(tri[0], dtype=np.float64)
        b = np.array(tri[1], dtype=np.float64)
        c = np.array(tri[2], dtype=np.float64)
        n = np.cross(b - a, c - a)
        if np.dot(n, (a + b + c)/3.0 - theCentre) < 0:
            b, c = c, b
            n = -n
        length = np.linalg.norm(n)
        if length == 0:
            continue #degenerate
        kept.append(t)
        for p in (a, b, c):
            if smooth:
                key = (round(p[0], 6), round(p[1], 6), round(p[2], 6))
            else:
                key = (round(p[0], 6), round(p[1], 6), round(p[2], 6), round(n[0]/length, 4), round(n[1]/length, 4), round(n[2]/length, 4))
            if key not in lookup:
                lookup[key] = len(positions)
                positions.append(p)
                normals.append(np.zeros(3))
            idx = lookup[key]
            normals[idx] = normals[idx] + n
            indices.append(idx)
    positions = np.array(positions, dtype=np.float32)
    normals = np.array(normals, dtype=np.float64)
    lengths = np.linalg.norm(normals, axis=1)
    lengths[lengths == 0] = 1.0
    normals = (normals/lengths[:, None]).astype(np.float32)
    indices = np.array(indices, dtype=np.uint32)
    return positions, normals, indices, kept

def makeIcosphere(subdivisions):
    #a unit sphere used for seeds. Much lighter than Sphere() (320 triangles
    #instead of 960), which matters because there can be thousands of seeds
    t = (1.0 + math.sqrt(5.0))/2.0
    verts = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
             (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
             (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
             (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
             (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
             (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    verts = [np.array(v, dtype=np.float64)/np.linalg.norm(v) for v in verts]
    for s in range(subdivisions):
        midCache = {}
        newFaces = []
        for f in faces:
            mids = []
            for k in range(3):
                i = f[k]
                j = f[(k + 1) % 3]
                key = (min(i, j), max(i, j))
                if key not in midCache:
                    m = verts[i] + verts[j]
                    verts.append(m/np.linalg.norm(m))
                    midCache[key] = len(verts) - 1
                mids.append(midCache[key])
            newFaces.append((f[0], mids[0], mids[2]))
            newFaces.append((f[1], mids[1], mids[0]))
            newFaces.append((f[2], mids[2], mids[1]))
            newFaces.append((mids[0], mids[1], mids[2]))
        faces = newFaces
    positions = np.array(verts, dtype=np.float32)
    normals = positions.copy() #unit sphere: normal == position
    indices = np.array(faces, dtype=np.uint32).reshape(-1)
    return positions, normals, indices


###########################################################################
#GLB writer

class GLBBuilder(object):
    def __init__(self):
        self.binary = bytearray()
        self.bufferViews = []
        self.accessors = []
        self.materials = []
        self.materialLookup = {}
        self.meshes = []
        self.nodes = []

    def _addBufferView(self, theBytes, target):
        while len(self.binary) % 4 != 0:
            self.binary.append(0)
        offset = len(self.binary)
        self.binary.extend(theBytes)
        self.bufferViews.append({"buffer": 0, "byteOffset": offset, "byteLength": len(theBytes), "target": target})
        return len(self.bufferViews) - 1

    def addVec3(self, theArray):
        theArray = np.ascontiguousarray(theArray, dtype=np.float32)
        view = self._addBufferView(theArray.tobytes(), ARRAY_BUFFER)
        self.accessors.append({"bufferView": view, "componentType": FLOAT, "count": int(theArray.shape[0]), "type": "VEC3",
                               "min": [float(v) for v in theArray.min(axis=0)], "max": [float(v) for v in theArray.max(axis=0)]})
        return len(self.accessors) - 1

    def addIndices(self, theArray):
        theArray = np.ascontiguousarray(theArray, dtype=np.uint32)
        view = self._addBufferView(theArray.tobytes(), ELEMENT_ARRAY_BUFFER)
        self.accessors.append({"bufferView": view, "componentType": UNSIGNED_INT, "count": int(theArray.shape[0]), "type": "SCALAR",
                               "min": [int(theArray.min())], "max": [int(theArray.max())]})
        return len(self.accessors) - 1

    def addGeometry(self, positions, normals, indices):
        return {"POSITION": self.addVec3(positions), "NORMAL": self.addVec3(normals)}, self.addIndices(indices)

    def material(self, theRGB, alpha=1.0):
        #theRGB is sRGB 0-1. One material per distinct colour
        key = (round(theRGB[0], 4), round(theRGB[1], 4), round(theRGB[2], 4), round(alpha, 3))
        if key not in self.materialLookup:
            m = {"name": "rgb_%02x%02x%02x" % (int(round(key[0]*255)), int(round(key[1]*255)), int(round(key[2]*255))),
                 "pbrMetallicRoughness": {"baseColorFactor": [srgbToLinear(key[0]), srgbToLinear(key[1]), srgbToLinear(key[2]), key[3]],
                                          "metallicFactor": 0.0, "roughnessFactor": 0.9},
                 "doubleSided": True}
            if alpha < 1.0:
                m["alphaMode"] = "BLEND"
            self.materials.append(m)
            self.materialLookup[key] = len(self.materials) - 1
        return self.materialLookup[key]

    def addMesh(self, name, primitives):
        #primitives: list of (attributes, indexAccessor, materialIndex)
        prims = []
        for p in primitives:
            prims.append({"attributes": p[0], "indices": p[1], "material": p[2], "mode": 4})
        self.meshes.append({"name": name, "primitives": prims})
        return len(self.meshes) - 1

    def addNode(self, theNode):
        self.nodes.append(theNode)
        return len(self.nodes) - 1

    def write(self, thePath, rootNodes):
        while len(self.binary) % 4 != 0:
            self.binary.append(0)
        theJSON = {"asset": {"version": "2.0", "generator": "Vida vglbGraphics"},
                   "scene": 0, "scenes": [{"nodes": rootNodes}],
                   "nodes": self.nodes, "meshes": self.meshes, "materials": self.materials,
                   "accessors": self.accessors, "bufferViews": self.bufferViews,
                   "buffers": [{"byteLength": len(self.binary)}]}
        jsonBytes = json.dumps(theJSON, separators=(",", ":")).encode("utf-8")
        while len(jsonBytes) % 4 != 0:
            jsonBytes = jsonBytes + b" "
        totalLength = 12 + 8 + len(jsonBytes) + 8 + len(self.binary)
        theFile = open(thePath, "wb")
        theFile.write(struct.pack("<III", 0x46546C67, 2, totalLength))   #"glTF", version 2
        theFile.write(struct.pack("<II", len(jsonBytes), 0x4E4F534A))   #JSON chunk
        theFile.write(jsonBytes)
        theFile.write(struct.pack("<II", len(self.binary), 0x004E4942)) #BIN chunk
        theFile.write(bytes(self.binary))
        theFile.close()


###########################################################################
#node helpers

def zRotationQuaternion(degrees):
    half = math.radians(degrees)/2.0
    return [0.0, 0.0, math.sin(half), math.cos(half)]

def trsNode(name, mesh, translation, scale, rotationDegrees=0.0):
    theNode = {"name": name, "mesh": mesh,
               "translation": [float(translation[0]), float(translation[1]), float(translation[2])],
               "scale": [float(scale[0]), float(scale[1]), float(scale[2])]}
    if rotationDegrees != 0.0:
        theNode["rotation"] = zRotationQuaternion(rotationDegrees)
    return theNode

def plantExtras(thePlant):
    #plant data that shows up as custom properties in Blender
    theExtras = {}
    for theAttr in ("name", "nameSpecies", "motherPlantName", "age", "heightStem", "radiusStem",
                    "radiusLeaf", "massStem", "massLeaf", "elevation", "crownShape", "x", "y"):
        if hasattr(thePlant, theAttr):
            theValue = getattr(thePlant, theAttr)
            if isinstance(theValue, (int, float, str, bool)):
                theExtras[theAttr] = theValue
    return theExtras


###########################################################################
#the parts of the scene that don't change between cycles

def initGLB(theGarden):
    #call once, like initDXFBlocks(). Builds the unit shapes and the terrain
    context = {}

    #box, used for the ground slab and the water slab (0-1 on each axis)
    tris, faceIdx = facesToTriangles(vdxfGraphics.Cube())
    context["box"] = weldTriangles(tris, (0.5, 0.5, 0.5), smooth=False)[0:3]

    #half sphere, used for stems and canopies (the same shape as the DXF)
    theCanopyFaces = vdxfGraphics.getCanopyFaceList()
    tris, faceIdx = facesToTriangles(theCanopyFaces)
    positions, normals, indices, kept = weldTriangles(tris, (-0.006944, 0.0, 0.0), smooth=True)
    context["dome"] = (positions, normals, indices)
    context["domeFaceCount"] = len(theCanopyFaces)
    #for each triangle in the dome, which DXF face it came from, so a canopy
    #can be split into leaf-coloured and species-coloured faces
    theTriangleFace = []
    for t in kept:
        theTriangleFace.append(faceIdx[t])
    context["domeTriangleFace"] = np.array(theTriangleFace)

    context["seed"] = makeIcosphere(2)

    #terrain
    context["terrain"] = None
    if len(theGarden.terrainImage) == 3:
        print("***Generating glb terrain mesh...***")
        context["terrain"] = makeTerrainGeometry(theGarden)
    return context

def makeTerrainGeometry(theGarden):
    #one vertex per pixel, same positions and heights as the DXF terrain
    #(pixel x,y is at world x-W/2, y-W/2), but as a single indexed mesh
    #with shared vertices and smooth normals
    theImage = theGarden.terrainImage
    theWorldSize = theGarden.theWorldSize
    thePixelRange = terrain_utils.getPixelRange(theGarden)
    pixels = np.array(Image.frombytes(theImage[0], theImage[1], theImage[2]))
    if pixels.ndim == 3:
        pixels = pixels[:, :, 0]
    size = theWorldSize
    heights = np.zeros((size, size), dtype=np.float64) #indexed [x][y]
    for x in range(size):
        px = min(x, pixels.shape[1] - 1)
        for y in range(size):
            py = min(y, pixels.shape[0] - 1)
            heights[x][y] = terrain_utils.elevationFromPixel(float(pixels[py][px]), theGarden.maxElevation, thePixelRange)
    xs, ys = np.meshgrid(np.arange(size, dtype=np.float64), np.arange(size, dtype=np.float64), indexing="ij")
    positions = np.stack([xs - theWorldSize/2.0, ys - theWorldSize/2.0, heights], axis=-1).reshape(-1, 3)

    #two triangles per grid cell, wound so normals point up (+z)
    indexList = []
    for x in range(size - 1):
        for y in range(size - 1):
            a = x*size + y
            b = (x + 1)*size + y
            c = (x + 1)*size + y + 1
            d = x*size + y + 1
            indexList.extend((a, b, c, a, c, d))
    indices = np.array(indexList, dtype=np.uint32)

    #smooth normals
    tri = indices.reshape(-1, 3)
    v0 = positions[tri[:, 0]]
    v1 = positions[tri[:, 1]]
    v2 = positions[tri[:, 2]]
    faceNormals = np.cross(v1 - v0, v2 - v0)
    normals = np.zeros_like(positions)
    for k in range(3):
        np.add.at(normals, tri[:, k], faceNormals)
    lengths = np.linalg.norm(normals, axis=1)
    lengths[lengths == 0] = 1.0
    normals = normals/lengths[:, None]
    return positions.astype(np.float32), normals.astype(np.float32), indices


###########################################################################
#one file per cycle

def writeGLB(outputDirectory, fileName, theGarden, context, waterStyle="solid"):
    if waterStyle not in WATER_STYLES:
        waterStyle = "solid"
    builder = GLBBuilder()
    theWorldSize = theGarden.theWorldSize
    half = theWorldSize/2.0
    children = []

    #shared shape buffers (the dome is only added if there are plants)
    boxAttr, boxIdx = builder.addGeometry(*context["box"])
    domeAttr = None
    domeIdx = None

    #ground
    groundMesh = builder.addMesh("ground", [(boxAttr, boxIdx, builder.material(GROUND_RGB))])
    children.append(builder.addNode(trsNode("ground", groundMesh, (-half, -half, 0.0), (theWorldSize, theWorldSize, 0.001))))

    #terrain and water
    if context["terrain"] is not None:
        tAttr, tIdx = builder.addGeometry(*context["terrain"])
        terrainMesh = builder.addMesh("terrain", [(tAttr, tIdx, builder.material(TERRAIN_RGB))])
        children.append(builder.addNode({"name": "terrain", "mesh": terrainMesh}))

        theWaterLevel = theGarden.waterLevel
        if isinstance(theWaterLevel, (int, float)) and theWaterLevel > 0.0 and waterStyle != "none":
            #both styles are a block of water from 0 up to the water level;
            #"translucent" makes it see-through so the flooded terrain shows
            #STH 2026-0926
            if waterStyle == "solid":
                waterMaterial = builder.material(WATER_RGB)
            else:
                waterMaterial = builder.material(WATER_RGB, WATER_TRANSLUCENT_ALPHA)
            waterMesh = builder.addMesh("water", [(boxAttr, boxIdx, waterMaterial)])
            children.append(builder.addNode(trsNode("water", waterMesh, (-half, -half, 0.0), (theWorldSize, theWorldSize, theWaterLevel))))

    #plants (one node each) and seeds (merged by colour)
    stemMeshes = {}
    canopyMeshes = {}
    seedGroups = {}
    plantNodes = []

    for obj in theGarden.soil:
        if obj.isSeed:
            r = obj.radiusSeed*obj.radiusSeedMultiplier
            addSeed(seedGroups, "dispersed", hsvToRGB(obj.colourSeedDispersed), (obj.x, obj.y, obj.elevation + r), r)
            continue

        if domeAttr is None:
            domeAttr, domeIdx = builder.addGeometry(*context["dome"])
        stemRadius = obj.radiusStem*obj.radiusStemMultiplier
        leafRadius = obj.radiusLeaf*obj.radiusLeafMultiplier
        leafRGB = hsvToRGB(obj.colourLeaf)
        speciesRGB = hsvToRGB(obj.colourSpecies)
        stemRGB = hsvToRGB(obj.colourStem)

        #stem
        stemMat = builder.material(stemRGB)
        if stemMat not in stemMeshes:
            stemMeshes[stemMat] = builder.addMesh("stem", [(domeAttr, domeIdx, stemMat)])
        stemNode = builder.addNode(trsNode("stem", stemMeshes[stemMat], (obj.x, obj.y, obj.elevation), (stemRadius, stemRadius, obj.heightStem)))

        #canopy, speckled with the species colour like the DXF version
        borderPercent = getattr(obj, "borderImagePercent", 0)
        canopyKey = (builder.material(leafRGB), builder.material(speciesRGB), borderPercent)
        if canopyKey not in canopyMeshes:
            canopyMeshes[canopyKey] = makeCanopyMesh(builder, context, domeAttr, canopyKey)
        if obj.crownShape == "PARA":
            boleFraction = obj.boleHeight/100.0
            canopyZ = obj.elevation + obj.heightStem - obj.heightStem*boleFraction
            canopyScale = (leafRadius, leafRadius, obj.heightStem*boleFraction)
        else:
            canopyZ = obj.elevation + obj.heightStem - leafRadius
            canopyScale = (leafRadius, leafRadius, leafRadius)
        canopyNode = builder.addNode(trsNode("canopy", canopyMeshes[canopyKey], (obj.x, obj.y, canopyZ), canopyScale, vdxfGraphics.getCanopyRotation(obj)))

        plantName = "%s %s" % (getattr(obj, "nameSpecies", "plant"), obj.name)
        plantNodes.append(builder.addNode({"name": plantName, "children": [stemNode, canopyNode], "extras": plantExtras(obj)}))

        for attachedSeed in obj.seedList:
            r = attachedSeed.radiusSeed*attachedSeed.radiusSeedMultiplier
            addSeed(seedGroups, "attached", hsvToRGB(obj.colourSeedAttached), (attachedSeed.x, attachedSeed.y, attachedSeed.z), r)

    if plantNodes:
        children.append(builder.addNode({"name": "plants", "children": plantNodes}))

    seedNodes = makeSeedNodes(builder, context, seedGroups)
    if seedNodes:
        children.append(builder.addNode({"name": "seeds", "children": seedNodes}))

    #rotate Vida's z-up world to glTF's y-up: (x, y, z) -> (x, z, -y)
    s = math.sqrt(0.5)
    root = builder.addNode({"name": "Vida", "rotation": [-s, 0.0, 0.0, s], "children": children,
                            "extras": {"cycle": getattr(theGarden, "cycleNumber", None), "worldSize": theWorldSize,
                                       "waterLevel": theGarden.waterLevel if isinstance(theGarden.waterLevel, (int, float)) else None}})
    builder.write(outputDirectory + fileName + ".glb", [root])

def makeCanopyMesh(builder, context, domeAttr, canopyKey):
    leafMat, speciesMat, borderPercent = canopyKey
    domeIndices = context["dome"][2].reshape(-1, 3)
    if borderPercent <= 0:
        return builder.addMesh("canopy", [(domeAttr, builder.addIndices(domeIndices.reshape(-1)), leafMat)])
    #pick which faces get the species colour, reproducibly for this combination
    #seeded by the colours (not material numbers) so the pattern is the same in every cycle's file
    theRNG = random.Random("%s_%s_%s" % (builder.materials[leafMat]["name"], builder.materials[speciesMat]["name"], borderPercent))
    isSpeciesFace = np.zeros(context["domeFaceCount"], dtype=bool)
    for i in range(context["domeFaceCount"]):
        if theRNG.random() < (borderPercent/100.0):
            isSpeciesFace[i] = True
    isSpeciesTriangle = isSpeciesFace[context["domeTriangleFace"]]
    primitives = []
    leafIdx = domeIndices[~isSpeciesTriangle].reshape(-1)
    speciesIdx = domeIndices[isSpeciesTriangle].reshape(-1)
    if leafIdx.size:
        primitives.append((domeAttr, builder.addIndices(leafIdx), leafMat))
    if speciesIdx.size:
        primitives.append((domeAttr, builder.addIndices(speciesIdx), speciesMat))
    return builder.addMesh("canopy", primitives)

def addSeed(seedGroups, kind, theRGB, centre, radius):
    key = (kind, round(theRGB[0], 4), round(theRGB[1], 4), round(theRGB[2], 4))
    if key not in seedGroups:
        seedGroups[key] = []
    seedGroups[key].append((centre[0], centre[1], centre[2], radius))

def makeSeedNodes(builder, context, seedGroups):
    #merge all seeds of one kind and colour into a single mesh
    unitPos, unitNrm, unitIdx = context["seed"]
    nVerts = unitPos.shape[0]
    theNodes = []
    for key in sorted(seedGroups.keys()):
        seeds = np.array(seedGroups[key], dtype=np.float64)
        centres = seeds[:, 0:3]
        radii = seeds[:, 3]
        positions = (unitPos[None, :, :]*radii[:, None, None] + centres[:, None, :]).reshape(-1, 3)
        normals = np.tile(unitNrm, (len(seeds), 1))
        offsets = (np.arange(len(seeds), dtype=np.uint32)*nVerts)[:, None]
        indices = (unitIdx[None, :] + offsets).reshape(-1)
        attr, idx = builder.addGeometry(positions, normals, indices)
        theName = "seeds_%s" % (key[0])
        theMesh = builder.addMesh(theName, [(attr, idx, builder.material((key[1], key[2], key[3])))])
        theNodes.append(builder.addNode({"name": theName, "mesh": theMesh, "extras": {"count": int(len(seeds))}}))
    return theNodes
