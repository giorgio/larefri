import ast
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace as S
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
TREE=ast.parse((ROOT/'app.py').read_text()); nodes=[]
for node in TREE.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='campo' for t in node.targets): break
    nodes.append(node)
exec(compile(ast.Module(body=nodes,type_ignores=[]),'app.py','exec'),{'__file__':str(ROOT/'app.py')})
import casa as c,nucleo as n,fotos as f
class Tests(unittest.TestCase):
    def test_all_seed_labels_deduplicated(self):
        nombres=['Arroz con huevo','Arroz con huevo (Campestre)','Arroz con huevo (Familiar)','Arroz con huevo (Criolla)','Arroz con huevo (Rápida)','Arroz con huevo (Costeña)']
        uno,dos=c.sin_recetas_repetidas([S(nombre=x) for x in nombres],[])
        self.assertEqual(len(uno),1)
        self.assertNotEqual(c.clave_receta('Arroz frito con huevo'),c.clave_receta('Arroz con huevo'))
        self.assertEqual(c.clave_receta('Arroz con pollo'),c.clave_receta('Pollo con arroz'))
    def test_spanish_and_dal_preserved(self):
        r=S(nombre='Dal',descripcion='Dal con guisantes',pasos=['Añadir patatas y boniato.'],ingredientes=[S(nombre='Patata',cantidad='1 patata',presentacion='1 patata')])
        n.localizar_receta(r)
        self.assertEqual(r.nombre,'Dal');self.assertIn('arveja',r.descripcion)
        self.assertIn('papa',r.pasos[0]);self.assertIn('camote',r.pasos[0])
    def test_refill_after_duplicate_batch(self):
        def recipe(name):
            return S(nombre=name,cocina="Internacional",plato_conocido=True,tiempo_minutos=20,
                     ingredientes=[S(nombre="Pollo",de_tu_casa=True),S(nombre="Arroz",de_tu_casa=True)],pasos=["Preparar"])
        cinco=[recipe("Plato " + str(i)) for i in range(5)]
        respuestas=[(S(recetas=cinco),"test"),(S(recetas=[recipe("Plato 0 (Campestre)")]),"test"),(S(recetas=[recipe("Plato 5")]),"test")]
        with patch.object(c,'recetas_de_la_memoria',return_value=[]),patch.object(c,'recetas_del_recetario',return_value=[]),patch.object(n,'llamar_gemini',side_effect=respuestas) as call,patch.object(n,'limpiar_receta',side_effect=lambda x:x),patch.object(n,'cumple_dieta',return_value=True),patch.object(c,'revisar',side_effect=lambda x,t:x),patch.object(c,'faltantes',return_value=[]):
            cero,uno=c.buscar_con_lo_que_hay(None,['Pollo','Arroz'],2,30)
        self.assertEqual(len(cero)+len(uno),6)
        self.assertEqual(call.call_count,3)

    def test_checks_commons_after_other_rejections(self):
        photo={'url':'commons.jpg','fuente':'Wikimedia Commons'}
        with patch.object(f,'foto_mealdb',return_value=None),patch.object(f,'candidatos_unsplash',return_value=[{'url':'bad.jpg','fuente':'Unsplash'}]),patch.object(f,'foto_pexels',return_value=None),patch.object(f,'foto_commons',return_value=photo) as commons:
            result=f.buscar_foto('chicken rice','pexels','unsplash',verificar=lambda url:url=='commons.jpg')
        self.assertEqual(result['url'],'commons.jpg');commons.assert_called_once()
    def test_outage_not_absence(self):
        with patch.object(f,'foto_mealdb',side_effect=f.ErrorFuente('caída')),patch.object(f,'foto_commons',return_value=None):
            with self.assertRaises(f.ErrorFuente):f.buscar_foto('rice')
    def test_real_photo_after_one_provider_outage(self):
        photo={'url':'commons.jpg','fuente':'Wikimedia Commons'}
        with patch.object(f,'foto_mealdb',side_effect=f.ErrorFuente('caída')),patch.object(f,'foto_commons',return_value=photo):
            self.assertEqual(f.buscar_foto('rice')['url'],'commons.jpg')
    def test_empty_completed_search_allows_fallback(self):
        with patch.object(f,'foto_mealdb',return_value=None),patch.object(f,'foto_commons',return_value=None):
            self.assertIsNone(f.buscar_foto('rice'))
    def test_error_does_not_generate_ai(self):
        fn=next(x for x in TREE.body if isinstance(x,ast.FunctionDef) and x.name=='_obtener_foto')
        ns={'_foto_de_fuentes':lambda r:{'_error':'Búsqueda incompleta'},'_imagen_ia':lambda r:self.fail('No debe generar IA')}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'app.py','exec'),ns)
        self.assertEqual(ns['_obtener_foto'](None),{'_error':'Búsqueda incompleta'})
if __name__=='__main__':unittest.main()
