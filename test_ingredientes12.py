import unittest
from unittest.mock import patch
from types import SimpleNamespace as S
from test_seis_y_fotos import c,n,r
import mealdb

class IngredientesTests(unittest.TestCase):
    def test_no_pasta_as_pantry(self):
        pasta=r('Espagueti con pollo','Italiana')
        pasta.ingredientes[1].nombre='Spaghetti'
        pasta.ingredientes[1].basico_de_despensa=True
        c.revisar(pasta,['Pollo','Arroz'])
        self.assertIn('Spaghetti',c.faltantes(pasta,['Pollo','Arroz']))
        self.assertFalse(c.compatible_con_seleccion(pasta,['Pollo','Arroz']))
        self.assertTrue(c.compatible_con_seleccion(pasta,['Pollo','Spaghetti']))
    def test_rice_required_even_with_selected_protein(self):
        dish=r('Pollo al horno','Internacional')
        dish.ingredientes=dish.ingredientes[:1]
        self.assertFalse(c.compatible_con_seleccion(dish,['Pollo','Arroz']))
    def test_four_plus_incompatible_are_replenished(self):
        valid=[r('Arroz prueba '+str(i),'Internacional') for i in range(6)]
        pasta=r('Spaghetti','Italiana');pasta.ingredientes[1].nombre='Spaghetti'
        with patch.object(c,'recetas_de_la_memoria',return_value=[]),patch.object(c,'recetas_del_recetario',return_value=[]),patch.object(n,'llamar_gemini',side_effect=[(S(recetas=valid[:4]+[pasta]),'test'),(S(recetas=valid[4:]),'test')]) as api:
            a,b=c.buscar_con_lo_que_hay(None,['Pollo','Arroz'],2,30)
        self.assertEqual(len(a+b),6)
        self.assertNotIn('Spaghetti',[x.nombre for x in a+b])
        self.assertEqual(api.call_count,2)
    def test_external_catalog_not_truncated_to_four(self):
        fixtures=[{'strMeal':str(i)} for i in range(12)]
        with patch.object(mealdb,'_get',return_value=[]),patch.object(mealdb,'de_spoonacular',return_value=fixtures) as search:
            results=mealdb.recetas_posibles(['Arroz'],maximo=24)
        self.assertEqual(len(results),12)
        self.assertEqual(search.call_args.kwargs['numero'],24)

if __name__=='__main__':unittest.main()
