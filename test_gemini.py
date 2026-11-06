import ast
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as S
from unittest.mock import patch
ROOT = Path(__file__).resolve().parent.parent
CODE = ROOT / 'corregido' if (ROOT / 'corregido').is_dir() else ROOT
sys.path.insert(0, str(CODE))
import nucleo as n
import casa as c
import fotos
from pydantic import BaseModel
class Respuesta(BaseModel):
    valor: str
class Fallo(Exception):
    def __init__(self, code): self.code=code
class Pruebas(unittest.TestCase):
    def test_fallback_y_schema(self):
        llamadas=[]
        def generar(**kw):
            llamadas.append(kw)
            if len(llamadas)==1: raise Fallo(404)
            return S(parsed=None,text='{"valor":"bien"}')
        obj, modelo=n.llamar_gemini(S(models=S(generate_content=generar)), 'hola', Respuesta,
                                    modelos=('no-disponible','gemini-2.5-flash'))
        self.assertEqual(obj.valor,'bien')
        self.assertEqual(llamadas[-1]['config'].thinking_config.thinking_budget,0)
    def test_cuota_no_se_oculta_por_404(self):
        def generar(**kw): raise Fallo(429 if kw['model']=='a' else 404)
        with self.assertRaisesRegex(n.ErrorIA,'429'):
            n.generar_con_respaldo(S(models=S(generate_content=generar)),'x',('a','b'))
    def test_permisos_sin_reintentos(self):
        with patch.object(n.time,'sleep') as espera:
            with self.assertRaisesRegex(n.ErrorIA,'403'):
                n.generar_con_respaldo(S(models=S(generate_content=lambda **kw: (_ for _ in ()).throw(Fallo(403)))),'x')
            espera.assert_not_called()
    def test_error_recetas_visible(self):
        with patch.object(n,'llamar_gemini',side_effect=n.ErrorIA('Cuota agotada')):
            with self.assertRaisesRegex(n.ErrorIA,'Cuota agotada'):
                c.buscar_con_lo_que_hay(None,['Arroz'],2,30,creativo=True)
    def test_recetario_se_conserva(self):
        receta=S(nombre='Arroz', ingredientes=[], pasos=['Cocer'])
        with patch.object(c,'recetas_de_la_memoria',return_value=[]), patch.object(c,'recetas_del_recetario',return_value=[receta]), patch.object(n,'llamar_gemini',side_effect=n.ErrorIA('Cuota')):
            cero,uno=c.buscar_con_lo_que_hay(None,['Arroz'],2,30)
        self.assertEqual(cero,[receta])
    def test_mime(self):
        self.assertEqual(n.mime_imagen(b'\x89PNG\r\n\x1a\n'), 'image/png')
        self.assertEqual(n.mime_imagen(b'RIFF1234WEBP'), 'image/webp')
        with self.assertRaises(n.ErrorIA): n.mime_imagen(b'<html>error</html>')
    def test_commons_con_cuota_vision_agotada(self):
        f=dict(url='https://example.org/a.jpg',fuente='Wikimedia Commons',_titulo='Tomato salad.jpg')
        with patch.object(fotos,'foto_commons',return_value=f):
            foto=fotos.buscar_foto('tomato salad', verificar=lambda url: None)
        self.assertEqual(foto['url'], f['url'])
        self.assertNotIn('_titulo',foto)
    def test_generacion_imagen_y_extraccion(self):
        import threading,time
        tree=ast.parse((CODE / 'app.py').read_text())
        func=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='crear_imagen')
        func.decorator_list=[]
        contador={}; llamadas=[]
        def generar(**kw):
            llamadas.append(kw)
            return S(candidates=[S(content=S(parts=[S(inline_data=S(data=b'\x89PNG\r\n\x1a\n',mime_type='image/png'))]))])
        ns=dict(n=n,time=time,_bloqueo_imagen=lambda:threading.Lock(),_creadas_hoy=lambda:contador,
                MAX_IMAGENES_DIA=30,MODELOS_IMAGEN=('gemini-2.5-flash-image',),
                cliente_gemini=lambda:S(models=S(generate_content=generar)))
        exec(compile(ast.Module(body=[func],type_ignores=[]),'app.py','exec'),ns)
        self.assertEqual(ns['crear_imagen']('Arroz','arroz'), b'\x89PNG\r\n\x1a\n')
        self.assertEqual(sum(contador.values()),1)
        self.assertIn('IMAGE', llamadas[0]['config'].response_modalities)
        contador[time.strftime('%Y-%m-%d')]=30
        with self.assertRaises(n.ErrorIA): ns['crear_imagen']('otro','arroz')
if __name__=='__main__': unittest.main()
