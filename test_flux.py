"""Pruebas sin claves ni consumo: cliente real, transporte HTTP simulado."""
import ast
import io
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
TREE=ast.parse((ROOT/'app.py').read_text())
CALL=next(x.value for x in TREE.body if isinstance(x,ast.Assign) and isinstance(x.value,ast.Call)
          and isinstance(x.value.func,ast.Name) and x.value.func.id=='_integrar_modulo'
          and x.value.args[0].value=='imagenes_flux')
f=types.ModuleType('flux_test');exec(CALL.args[1].value,f.__dict__)
KEY='sk_test_NOT_A_REAL_KEY'
buffer=io.BytesIO();Image.new('RGB',(8,8),'orange').save(buffer,format='PNG');PNG=buffer.getvalue()
class Response:
    def __init__(self,status=200,data=PNG,content_type='image/png'):
        self.status_code=status;self.content=data;self.headers={'Content-Type':content_type};self.closed=False
    def close(self):self.closed=True
class Tests(unittest.TestCase):
    def test_success_and_private_auth(self):
        reply=Response()
        with patch.object(f.requests,'get',return_value=reply) as get:
            self.assertEqual(f.generar('Pollo con arroz','pollo, arroz',KEY),PNG)
            url=get.call_args.args[0];opts=get.call_args.kwargs
            self.assertTrue(url.startswith('https://gen.pollinations.ai/image/'))
            self.assertNotIn(KEY,url);self.assertNotIn(KEY,str(opts['params']))
            self.assertEqual(opts['headers']['Authorization'],'Bearer '+KEY)
            self.assertEqual(opts['params']['model'],f.MODELO)
            self.assertFalse(opts['allow_redirects']);self.assertTrue(reply.closed)
    def test_no_key_no_request(self):
        with patch.object(f.requests,'get') as get:
            for key in ('','pk_example'):
                with self.assertRaises(f.ErrorImagen): f.generar('arroz','arroz',key)
            get.assert_not_called()
    def test_status_messages_no_raw_error(self):
        for status in (400,401,402,403,404,429,503,302):
            with self.subTest(status=status),patch.object(f.requests,'get',return_value=Response(status,KEY.encode())) as get:
                with self.assertRaises(f.ErrorImagen) as caught: f.generar('arroz','arroz',KEY)
                self.assertNotIn(KEY,str(caught.exception));self.assertEqual(get.call_count,1)
    def test_timeout_no_hidden_retry(self):
        with patch.object(f.requests,'get',side_effect=f.requests.Timeout(KEY)) as get:
            with self.assertRaises(f.ErrorImagen) as caught:f.generar('arroz','arroz',KEY)
            self.assertNotIn(KEY,str(caught.exception));self.assertEqual(get.call_count,1)
    def test_network_error_safe(self):
        with patch.object(f.requests,'get',side_effect=f.requests.ConnectionError(KEY)):
            with self.assertRaises(f.ErrorImagen) as caught:f.generar('arroz','arroz',KEY)
            self.assertNotIn(KEY,str(caught.exception))
    def test_reject_html_and_corrupt_image(self):
        for reply in (Response(data=b'<html>error</html>',content_type='text/html'),Response(data=b'not a PNG')):
            with patch.object(f.requests,'get',return_value=reply):
                with self.assertRaises(f.ErrorImagen):f.generar('arroz','arroz',KEY)
                self.assertTrue(reply.closed)
    def test_image_wrapper_keeps_errors(self):
        fn=next(x for x in TREE.body if isinstance(x,ast.FunctionDef) and x.name=='_imagen_ia')
        ns={'_flux':f,'crear_imagen':lambda *a, **kw: (_ for _ in ()).throw(f.ErrorImagen('Falta clave'))}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'app.py','exec'),ns)
        recipe=types.SimpleNamespace(nombre='Arroz',ingredientes=[])
        self.assertEqual(ns['_imagen_ia'](recipe),{'_error':'Falta clave'})
    def test_cached_failure_does_not_call_provider_again(self):
        class UI:
            session_state={'_errores_fotos':{'test':{'_error':'Sin saldo'}}}
        ns={'st':UI,'_clave_foto':lambda r:'test','_imagen_ia':lambda r:self.fail('No debe reintentar solo')}
        fn=next(x for x in TREE.body if isinstance(x,ast.FunctionDef) and x.name=='_buscar_foto')
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'app.py','exec'),ns)
        self.assertEqual(ns['_buscar_foto'](None),{'_error':'Sin saldo'})
if __name__=='__main__':unittest.main()
