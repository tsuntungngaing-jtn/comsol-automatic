"""Original benchmark fixtures. Import and call ONLY inside comsol_model_code.

This module does not start a COMSOL process. The caller provides a fresh tracked
MPh model and the validation modules from the tested checkout.
"""
from pathlib import Path
import hashlib
import json
from time import perf_counter
from uuid import uuid4


def box_selection(comp, tag, dimension, bounds):
    selection=comp.selection().create(tag,'Box')
    selection.set('entitydim',str(dimension));selection.set('condition','inside')
    for name,value in bounds.items():selection.set(name,str(value))
    return {'id':tag,'tag':tag,'dimension':dimension,'count':{'reference':1},'allow_empty':False,
            'purpose':'Benchmark spatial boundary; re-evaluate after every rebuild'}


def build(model, task):
    java=model.java
    if list(java.component().tags()):raise ValueError('Fresh empty model required')
    comp=java.component().create('comp1',True)
    dim=2 if task in ('laminar_channel','kepsilon_channel') else 3
    geom=comp.geom().create('geom1',dim)
    geom.lengthUnit('m' if task in ('heat_conduction','solid_convection','laminar_channel','kepsilon_channel') else 'mm')
    selections=[]
    if task in ('simple_block','selection_rebind'):
        java.param().set('w','10[mm]')
        block=geom.create('blk','Block');block.set('size',['w','20[mm]','30[mm]' if task=='simple_block' else '10[mm]'])
        selections.append(box_selection(comp,'left',2,{'xmin':'-1e-6','xmax':'1e-6'}))
    elif task=='boolean_channel':
        block=geom.create('outer','Block');block.set('size',['10','2','2'])
        cut=geom.create('inner','Block');cut.set('size',['10','1','1']);cut.set('pos',['0','0.5','0.5'])
        difference=geom.create('channel','Difference');difference.selection('input').set(['outer']);difference.selection('input2').set(['inner'])
    elif task=='parameter_array':
        java.param().set('n','3')
        block=geom.create('device','Block');block.set('size',['1','1','1'])
        array=geom.create('devices','Array');array.selection('input').set(['device']);array.set('size',['n','1','1']);array.set('displ',['2','0','0'])
    elif task=='rotate_180':
        java.param().set('theta','180[deg]')
        block=geom.create('device','Block');block.set('size',['2','1','1']);block.set('pos',['2','1','0'])
        marker=geom.create('orientation_marker','Block');marker.set('size',['0.25','0.25','0.25']);marker.set('pos',['3.75','1.75','1'])
        union=geom.create('marked_device','Union');union.selection('input').set(['device','orientation_marker']);union.set('intbnd','off')
        rotate=geom.create('turn','Rotate');rotate.selection('input').set(['marked_device']);rotate.set('axis',['0','0','1']);rotate.set('rot','theta')
        selections.append(box_selection(comp,'tip',2,{'zmin':'1.249999','zmax':'1.250001'}))
        selections[0]['measurements']=[{'metric':'bbox','reference':[-4,-3.75,-2,-1.75,1.25,1.25],'atol':1e-7}]
    elif dim==3:
        block=geom.create('solid','Block');block.set('size',['0.01','0.01','0.01'])
        selections.append(box_selection(comp,'left',2,{'xmin':'-1e-9','xmax':'1e-9'}))
        selections.append(box_selection(comp,'right',2,{'xmin':'0.009999999','xmax':'0.010000001'}))
    else:
        block=geom.create('channel','Rectangle');block.set('size',['1','0.1'])
        selections.append(box_selection(comp,'inlet',1,{'xmin':'-1e-9','xmax':'1e-9'}))
        selections.append(box_selection(comp,'outlet',1,{'xmin':'0.999999999','xmax':'1.000000001'}))
    geom.run()
    return selections


def configure_physics(model, task, library):
    comp=model.java.component('comp1');geom=comp.geom('geom1')
    fluid=task in ('laminar_channel','kepsilon_channel')
    material='air' if fluid else 'copper'
    inserted=comp.material().insert(str(library),[material])
    comp.material(material).selection().all()
    warnings=[str(x) for x in inserted[0]]
    if warnings:raise RuntimeError('Material import messages require review: '+repr(warnings))
    if fluid:
        kind='LaminarFlow' if task=='laminar_channel' else 'TurbulentFlowkeps'
        physics=comp.physics().create('spf',kind,'geom1')
        inlet=physics.create('inl','Inlet' if task=='laminar_channel' else 'InletBoundary',1);inlet.selection().named('inlet')
        inlet.set('U0in','6*0.01[m/s]*(y/0.1[m])*(1-y/0.1[m])' if task=='laminar_channel' else '2[m/s]')
        if task=='kepsilon_channel':
            inlet.set('RANSVarOption','SpecifyTurbulentLengthScaleAndIntensity')
            inlet.set('IT_list','user_defined');inlet.set('IT','0.05')
            inlet.set('LT_list','user_defined');inlet.set('LT','0.007[m]')
        outlet=physics.create('out','Outlet' if task=='laminar_channel' else 'OutletBoundary',1);outlet.selection().named('outlet');outlet.set('p0','0[Pa]')
    else:
        physics=comp.physics().create('ht','HeatTransfer','geom1')
        if task=='heat_conduction':
            for name,temperature in [('left','293.15[K]'),('right','393.15[K]')]:
                node=physics.create(name,'TemperatureBoundary',2);node.selection().named(name);node.set('T0',temperature)
        else:
            source=physics.create('source','HeatSource',3);source.selection().all();source.set('Q0','1e5[W/m^3]')
            flux=physics.create('cool','HeatFluxBoundary',2);flux.selection().all();flux.set('HeatFluxType','ConvectiveHeatFlux');flux.set('h','10[W/(m^2*K)]');flux.set('Text','293.15[K]')
    mesh=comp.mesh().create('mesh1','geom1');mesh.autoMeshSize(8 if task=='kepsilon_channel' else 4);mesh.run()
    study=model.java.study().create('std1');study.create('stat','Stationary')
    return {'physics_type':str(physics.getType()),'material':material,'study_label':str(study.label())}


def evaluate(model, task):
    java=model.java
    def derived(tag,kind,expression,selection=None):
        if tag in [str(t) for t in java.result().numerical().tags()]:java.result().numerical().remove(tag)
        node=java.result().numerical().create(tag,kind);node.set('expr',expression)
        if selection:node.selection().named(selection)
        else:node.selection().all()
        return float(node.getReal()[0][0])
    if task in ('heat_conduction','solid_convection'):
        average=derived('avg','AvVolume' if task=='heat_conduction' else 'AvSurface','T')
        if task=='solid_convection':
            incoming=derived('qin','IntVolume','ht.Q');outgoing=derived('qout','IntSurface','ht.ntflux')
        else:
            incoming=-derived('qin','IntSurface','ht.ntflux','right');outgoing=derived('qout','IntSurface','ht.ntflux','left')
        return {'temperature_K':average,'inflow_W':incoming,'outflow_W':outgoing,'relative_balance':abs(incoming-outgoing)/max(abs(incoming),abs(outgoing),1e-30)}
    incoming=derived('minlet','IntLine','spf.rho*(u*nx+v*ny)','inlet')
    outgoing=derived('moutlet','IntLine','spf.rho*(u*nx+v*ny)','outlet')
    result={'inflow_kg_per_m_s':incoming,'outflow_kg_per_m_s':outgoing,'relative_balance':abs(incoming+outgoing)/max(abs(incoming),abs(outgoing),1e-30)}
    if task=='laminar_channel':
        # Area mean for a fully developed planar profile is exactly Umean.
        result['mean_velocity_m_s']=derived('umean','AvSurface','u')
    return result
