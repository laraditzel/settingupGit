# 
# ------------------------------------------------ Libraries

from abaqus import *
from abaqusConstants import *
import assembly
import mesh

# ------------------------------------------------ Define Model
# Create a model
model = mdb.Model(name='ContactPairsModel')

# ------------------------------------------------ Material Properties
# Aluminum 20.20.433
model.Material(name='Aluminum')
model.materials['Aluminum'].Density(table=((2.77e-9,),))  # Density in tonnes/mm^3
model.materials['Aluminum'].Elastic(table=((73.1e3, 0.33),))  # Elastic modulus in N/mm^2 and Poisson's ratio

# Steel AISI A1005
model.Material(name='Steel')
model.materials['Steel'].Density(table=((7.85e-9,),))  # Density in tonnes/mm^3
model.materials['Steel'].Elastic(table=((200e3, 0.29),))  # Elastic modulus in N/mm^2 and Poisson's ratio

# ------------------------------------------------ Parts
# Create Plank
plank_sketch = model.ConstrainedSketch(
        name='PlankSketch', 
        sheetSize=200.0)
plank_sketch.rectangle(point1=(-40.0, 0.0), point2=(40.0, 2.0))
plank_part = model.Part(
        name='Plank', 
        dimensionality=THREE_D, 
        type=DEFORMABLE_BODY)
plank_part.BaseSolidExtrude(sketch=plank_sketch, depth=20.0)

# Create Curved Block
curved_sketch = model.ConstrainedSketch(
        name='CurvedSketch', 
        sheetSize=200.0)
curved_sketch.CircleByCenterPerimeter(center=(0.0,0.0), point1=(10.0,0.0))
curved_sketch.rectangle(point1=(-10.0, 0.0), point2=(10.0, -15.0))
g = curved_sketch.geometry
curved_sketch.autoTrimCurve(curve1=g[2], point1=(0.0,-10.0))
curved_sketch.autoTrimCurve(curve1=g[6], point1=(0.0, 0.0))
curvedBlock_part = model.Part(
        name='CurvedBlock', 
        dimensionality=THREE_D, 
        type=DEFORMABLE_BODY)
curvedBlock_part.BaseSolidExtrude(sketch=curved_sketch, depth=20.0)

# Create Rectangular Block
rectangular_sketch = model.ConstrainedSketch(
        name='RectangularSketch', 
        sheetSize=200.0)
rectangular_sketch.rectangle(point1=(0.0, 0.0), point2=(35.0, 10.0))
rectangularBlock_part = model.Part(
        name='RectangularBlock', 
        dimensionality=THREE_D, 
        type=DEFORMABLE_BODY)
rectangularBlock_part.BaseSolidExtrude(sketch=rectangular_sketch, depth=20.0)

# ------------------------------------------------ Assign Materials
model.HomogeneousSolidSection(
        name='AluminumSection', 
        material='Aluminum', 
        thickness=None)
model.HomogeneousSolidSection(
        name='SteelSection', 
        material='Steel', 
        thickness=None)

plank_region = (plank_part.cells,)
plank_part.SectionAssignment(
        region=plank_region, 
        sectionName='AluminumSection', 
        offset=0.0, 
        offsetType=MIDDLE_SURFACE, 
        offsetField='', 
        thicknessAssignment=FROM_SECTION)

curvedBlock_region = (curvedBlock_part.cells,)
curvedBlock_part.SectionAssignment(
        region=curvedBlock_region,
        sectionName='SteelSection', 
        offset=0.0,                              
        offsetType=MIDDLE_SURFACE, 
        offsetField='', 
        thicknessAssignment=FROM_SECTION)

rectangularBlock_region = (rectangularBlock_part.cells,)
rectangularBlock_part.SectionAssignment(
        region=rectangularBlock_region, 
        sectionName='SteelSection',
        offset=0.0,                             
        offsetType=MIDDLE_SURFACE, 
        offsetField='', 
        thicknessAssignment=FROM_SECTION)

# ------------------------------------------------ Assembly
assembly = model.rootAssembly
assembly.Instance(
        name='curvedBlockInstance', 
        part=curvedBlock_part, 
        dependent=ON)
assembly.Instance(
        name='plankInstance', 
        part=plank_part, 
        dependent=ON)
assembly.Instance(
        name='rectangularBlockInstance', 
        part=rectangularBlock_part, 
        dependent=ON)

# Positioning
assembly.translate(instanceList=('plankInstance',), vector=(0.0, 10.0, 0.0)) 
assembly.translate(instanceList=('rectangularBlockInstance',), vector=(5.0, 12.0, 0.0)) 

# ------------------------------------------------ Step Creation
model.StaticStep(
        name='MakeContact', 
        previous='Initial', 
        description='Push parts together to avoid chatter', 
        initialInc=0.1, 
        nlgeom=ON)
model.StaticStep(
        name='ApplyForce',
        previous='MakeContact', 
        description='Apply force on one end of the plank', 
        initialInc=0.1,
        nlgeom=ON)

# ------------------------------------------------ Boundary Conditions

# Defininng Surfaces and Regions for BC
curvedBlock_bottom_surface = assembly.instances['curvedBlockInstance'].faces.findAt(((0.0,-15.0,10.0),))
curvedBlock_bottom_region  = assembly.Set(faces=curvedBlock_bottom_surface, name='Set_curvedBlock_bottom')
assembly.Surface(side1Faces=curvedBlock_bottom_surface, name='curvedBlock_bottom')


rectangularBlock_side_surface = assembly.instances['rectangularBlockInstance'].faces.findAt(((40.0,21.0,10.0),))
rectangularBlock_side_region  = assembly.Set(faces=rectangularBlock_side_surface, name='Set_rectangularBlock_side')
assembly.Surface(side1Faces=rectangularBlock_side_surface, name='rectangularBlock_side')

plank_side_surface = assembly.instances['plankInstance'].faces.findAt(((40.0,11.0,10.0),))
plank_side_region  = assembly.Set(faces=plank_side_surface, name='Set_plank_side')
assembly.Surface(side1Faces=plank_side_surface, name='plank_side')

plank_top_surface = assembly.instances['plankInstance'].faces.findAt(((10.0,12.0,10.0),))
plank_top_region  = assembly.Set(faces=plank_top_surface, name='Set_plank_top')
assembly.Surface(side1Faces=plank_top_surface, name='plank_top')

rectangularBlock_top_surface = assembly.instances['rectangularBlockInstance'].faces.findAt(((10.0,22.0,10.0),))
rectangularBlock_top_region  = assembly.Set(faces=rectangularBlock_top_surface, name='Set_rectangularBlock_top')
assembly.Surface(side1Faces=rectangularBlock_top_surface, name='rectangularBlock_top')


# Fix Curved Block at the Bottom
model.EncastreBC(
        name="FixedCurvedBlock", 
        createStepName='Initial', 
        region=curvedBlock_bottom_region, 
        localCsys=None)


# Fix Rectangular Block at the extreme side
model.EncastreBC(
        name="FixedRectangularBlock", 
        createStepName='ApplyForce', 
        region=rectangularBlock_side_region, 
        localCsys=None)

# Fix Plank at the extreme side
model.EncastreBC(
        name="FixedPlank", 
        createStepName='ApplyForce', 
        region=plank_side_region, 
localCsys=None)

# Fix Rectangular Block at the extreme side after contact
model.DisplacementBC(
        name='PressPlank-and-curvedBlock', 
        createStepName='MakeContact', 
        region=plank_top_region,
        u1= 0.0, u2= -0.2, u3= 0.0,
        ur1=0.0, ur2=0.0, ur3=0.0,
        amplitude=UNSET,
        fixed=OFF,
        distributionType=UNIFORM,
        fieldName='',
        localCsys=None)
model.boundaryConditions['PressPlank-and-curvedBlock'].deactivate('ApplyForce')

# Fix Plank at the extreme side after contact
model.DisplacementBC(
        name="PressRectangularBlock-and-Plank", 
        createStepName='MakeContact', 
        region=rectangularBlock_top_region,
        u1= 0.0, u2= -0.21, u3= 0.0,
        ur1=0.0, ur2=0.0, ur3=0.0,
        amplitude=UNSET,
        fixed=OFF,
        distributionType=UNIFORM,
        fieldName='',
        localCsys=None)

model.boundaryConditions['PressRectangularBlock-and-Plank'].deactivate('ApplyForce')

# ------------------------------------------------ Concentrated Forces

# Find the relevant vertices
points = (-40.0,10.0,0.0),(-40.0,10.0,20.0)
tuple_points = tuple([(p,) for p in points])
plank_bottom_vertices = assembly.instances['plankInstance'].vertices.findAt(*tuple_points)
plank_bottom_vertices_region  = assembly.Set(vertices=plank_bottom_vertices, name='Set_plank_bottom_vertices')

# Apply Point Loads
model.ConcentratedForce(
        name='ConcentratedForces',
        createStepName='ApplyForce',
        region=plank_bottom_vertices_region,
        cf2 = -4.0e1,
        distributionType=UNIFORM,
        field='',
        localCsys=None)

# ------------------------------------------------ Contact Properties

# Define Surfaces for Contact

curvedBlock_top_surface = assembly.instances['curvedBlockInstance'].faces.findAt(((0.0,10.0,10.0),))
curvedBlock_top_region  = assembly.Set(
        faces=curvedBlock_top_surface, 
        name='Set_curvedBlock_top')
assembly.Surface(side1Faces=curvedBlock_top_surface, name='curvedBlock_top')

plank_bottom_surface = assembly.instances['plankInstance'].faces.findAt(((0.0,10.0,10.0),))
plank_bottom_region  = assembly.Set(faces=plank_bottom_surface, name='Set_plank_bottom')
assembly.Surface(side1Faces=plank_bottom_surface, name='plank_bottom')

rectangularBlock_bottom_surface = assembly.instances['rectangularBlockInstance'].faces.findAt(((20.0,12.0,10.0),))
rectangularBlock_bottom_region  = assembly.Set(faces=rectangularBlock_bottom_surface, name='Set_rectangularBlock_bottom')
assembly.Surface(side1Faces=rectangularBlock_bottom_surface, name='rectangularBlock_bottom')

# Define Frictionless Contact

model.ContactProperty('Frictionless')
model.interactionProperties['Frictionless'].TangentialBehavior(
        formulation=FRICTIONLESS)

# Define Frictional Contact
model.ContactProperty('Frictional')
model.interactionProperties['Frictional'].TangentialBehavior(
        formulation=PENALTY,
        directionality=ISOTROPIC,
        slipRateDependency=OFF,
        pressureDependency=OFF,
        temperatureDependency=OFF,
        dependencies=0,
        table=((0.1,),),
        shearStressLimit=None,
        maximumElasticSlip=FRACTION,
        fraction=0.005,
        elasticSlipStiffness=None)

# Apply Frictionless Contact between curved Block and Plank
model.SurfaceToSurfaceContactStd(
        name='Interaction_curvedBlock_plank',
        createStepName='MakeContact',
        main=assembly.surfaces['curvedBlock_top'],
        secondary=assembly.surfaces['plank_bottom'],
        sliding=FINITE,
        thickness=ON,
        interactionProperty='Frictionless',
        adjustMethod=NONE,
        initialClearance=OMIT,
        datumAxis=None,
        clearanceRegion=None)

# Apply Frictional Contact between rectangular Block and Plank
model.SurfaceToSurfaceContactStd(
        name='Interaction_rectangularBlock_plank',
        createStepName='MakeContact',
        main=assembly.surfaces['rectangularBlock_bottom'],
        secondary=assembly.surfaces['plank_top'],
        sliding=FINITE,
        thickness=ON,
        interactionProperty='Frictional',
        adjustMethod=NONE,
        initialClearance=OMIT,
        datumAxis=None,
        clearanceRegion=None)

# ------------------------------------------------ Meshing Parts

# Define Element Types
elemType1 = mesh.ElemType(
        elemCode=C3D8R,
        elemLibrary=STANDARD,
        kinematicSplit=AVERAGE_STRAIN, 
        secondOrderAccuracy=OFF, 
        hourglassControl=DEFAULT, 
        distortionControl=DEFAULT)
elemType2 = mesh.ElemType(
        elemCode=C3D6,
        elemLibrary=STANDARD)
elemType3 = mesh.ElemType(
        elemCode=C3D4,
        elemLibrary=STANDARD)

curvedBlock_part.setElementType(
        regions=(curvedBlock_part.cells, ), 
        elemTypes=(elemType1, elemType2, elemType3))
curvedBlock_part.seedPart(
        size=1.25,
        deviationFactor=0.1,
        minSizeFactor=0.1)
curvedBlock_part.generateMesh()


rectangularBlock_part.setElementType(
        regions=(rectangularBlock_part.cells, ), 
        elemTypes=(elemType1, elemType2, elemType3))
rectangularBlock_part.seedPart(
        size=1.25,
        deviationFactor=0.1,
        minSizeFactor=0.1)
rectangularBlock_part.generateMesh()

plank_part.setElementType(
        regions=(plank_part.cells, ), 
        elemTypes=(elemType1, elemType2, elemType3))
plank_part.seedPart(
        size=1.25,
        deviationFactor=0.1,
        minSizeFactor=0.1)
plank_part.generateMesh()

# ------------------------------------------------ Job Submission

job = mdb.Job(name='250103-01_ContactSimulation', model=model, numCpus=4, numDomains=4)
"""
job.submit(consistencyChecking=ON)
job.waitForCompletion()
"""
