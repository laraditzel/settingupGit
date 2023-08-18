#Code based on https://github.com/haiiliin/pyabaqus/blob/main/tests/compression/compression-jupyter.ipynb

from abaqus import *
from abaqusConstants import *
from caeModules import *
from driverUtils import *

executeOnCaeStartup()

model = mdb.models['Model-1']

sketch = model.ConstrainedSketch(name='sketch', sheetSize=1.0)
sketch.rectangle((0, 0), (1, 1))

part = model.Part(name='part', dimensionality=THREE_D, type=DEFORMABLE_BODY)
part.BaseSolidExtrude(sketch=sketch, depth=1)
#BC
part.Set(name='set-all', cells=part.cells.findAt(coordinates=((0.5, 0.5, 0.5), )))
part.Set(name='set-bottom', faces=part.faces.findAt(coordinates=((0.5, 0.5, 0.0), )))
part.Set(name='set-top', faces=part.faces.findAt(coordinates=((0.5, 0.5, 1.0), )))
part.Surface(name='surface-top', side1Faces=part.faces.findAt(coordinates=((0.5, 0.5, 1.0), )))

model.rootAssembly.DatumCsysByDefault(CARTESIAN)
model.rootAssembly.Instance(name='instance', part=part, dependent=ON)

material = model.Material(name='material')

material.Elastic(table=((1000, 0.2), ))
material.Density(table=((2500, ), ))

model.HomogeneousSolidSection(name='section', material='material', thickness=None)
part.SectionAssignment(region=part.sets['set-all'], sectionName='section')

step = model.StaticStep(name='Step-1', previous='Initial', description='',
                        timePeriod=1.0, timeIncrementationMethod=AUTOMATIC,
                        maxNumInc=100, initialInc=0.01, minInc=0.001, maxInc=0.1) 

field = model.FieldOutputRequest('F-Output-1', createStepName='Step-1', variables=('S', 'E', 'U'))

#Create boundary conditions
bottom_instance = model.rootAssembly.instances['instance'].sets['set-bottom']
bc = model.DisplacementBC(name='BC-1', createStepName='Initial', region=bottom_instance, u3=SET)

#Pressure
top_instance = model.rootAssembly.instances['instance'].surfaces['surface-top']
pressure = model.Pressure('pressure', createStepName='Step-1', region=top_instance, magnitude=100)


import mesh

elem1 = mesh.ElemType(elemCode=C3D8R)
elem2 = mesh.ElemType(elemCode=C3D6)
elem3 = mesh.ElemType(elemCode=C3D4)
part.setElementType(regions=(part.cells, ), elemTypes=(elem1, elem2, elem3))
part.seedPart(size=0.1)
part.generateMesh()


job = mdb.Job(name='Job-10', model='Model-1')
job.writeInput()
job.submit()
job.waitForCompletion()

mdb.saveAs('compression.cae')
