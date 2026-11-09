import ast
import sys
from pathlib import Path
from types import SimpleNamespace as S
from unittest.mock import patch
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TREE=ast.parse((ROOT/'app.py').read_text())
statements=[]
for node in TREE.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='campo' for t in node.targets):break
    statements.append(node)
exec(compile(ast.Module(body=statements,type_ignores=[]),'app.py','exec'),{'__file__':str(ROOT/'app.py')})
import casa as c
import nucleo as n

def r(nombre,pais,missing=False):
    # Fixtures for routing only, not full culinary descriptions.
    ingredientes=[c.IngredienteCasa(nombre=x,cantidad='1',presentacion='unidad',precio_presentacion_usd=1,fraccion_usada=1,basico_de_despensa=False,de_tu_casa=True) for x in ('Pollo','Arroz')]
    if missing:ingredientes.append(c.IngredienteCasa(nombre='Salsa de soya',cantidad='1',presentacion='frasco',precio_presentacion_usd=1,fraccion_usada=.1,basico_de_despensa=False,de_tu_casa=False))
    return c.RecetaCasa(nombre=nombre,cocina=pais,descripcion='Plato',porciones=2,tiempo_minutos=25,dificultad='Fácil',etiquetas=[],ingredientes=ingredientes,pasos=['Preparar'],calorias_por_porcion=300,proteina_g_por_porcion=20,por_que_es_saludable='',busqueda_foto='chicken rice',icono='pollo')
class Tests(unittest.TestCase):
    def test_six_even_with_shared_missing_ingredient(self):
        recipes=[r('Seco de pollo','Ecuatoriana')]+[r('Plato de prueba '+str(i),'Internacional',True) for i in range(5)]
        with patch.object(c,'recetas_de_la_memoria',return_value=[]),patch.object(c,'recetas_del_recetario',return_value=[]),patch.object(n,'llamar_gemini',return_value=(S(recetas=recipes),'test')):
            cero,uno=c.buscar_con_lo_que_hay(None,['Pollo','Arroz'],2,30)
        self.assertEqual((len(cero),len(uno)),(1,5))
    def test_no_ecuador_preference_and_variety(self):
        recipes=[r('A arroz','Ecuatoriana'),r('B arroz','Ecuatoriana'),r('Z arroz','Japonesa')]
        cero,uno=c.seleccionar_seis(recipes,[],['Pollo','Arroz'],2)
        self.assertEqual({x.cocina for x in cero},{'Ecuatoriana','Japonesa'})
        recipes=[r('Z arroz','Ecuatoriana'),r('A arroz','Japonesa')]
        self.assertEqual(c.seleccionar_seis(recipes,[],['Pollo','Arroz'],1)[0][0].cocina,'Japonesa')
    def test_recipes_not_duplicated(self):
        recipes=[r('Arroz con pollo (Casera)','Ecuatoriana'),r('Arroz con pollo (Andina)','Ecuatoriana')]
        cero,uno=c.seleccionar_seis(recipes,[],['Pollo','Arroz'])
        self.assertEqual(len(cero),1)
    def test_stock_before_flux(self):
        fn=next(x for x in TREE.body if isinstance(x,ast.FunctionDef) and x.name=='_obtener_foto')
        stock=S();generated=S();calls=[]
        ns={'_foto_de_fuentes':lambda r:stock,'_imagen_ia':lambda r:calls.append(r) or generated}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'app.py','exec'),ns)
        self.assertIs(ns['_obtener_foto']('recipe'),stock);self.assertEqual(calls,[])
        ns['_foto_de_fuentes']=lambda r:None
        self.assertIs(ns['_obtener_foto']('recipe'),generated);self.assertEqual(calls,['recipe'])
    def test_stored_recipe_set_current_example(self):
        with patch.object(c,'recetas_del_recetario',return_value=[]),patch.object(n,'llamar_gemini',return_value=(S(recetas=[]),'test')):
            cero,uno=c.buscar_con_lo_que_hay(None,['Pollo','Arroz'],2,45)
        self.assertEqual(len(cero)+len(uno),6)
if __name__=='__main__':unittest.main()
