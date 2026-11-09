import ast,json,unittest
from types import SimpleNamespace as S
from unittest.mock import Mock,patch
from urllib.parse import unquote
from test_flux import TREE,f,Response,KEY

PROMPT='Realistic food photograph of thick brown lentil stew beside a separate portion of plain white rice. Cooked onion, tomato and garlic are integrated into the stew, with no raw garnish. Natural light, three-quarter angle, no text or people.'
class PromptTests(unittest.TestCase):
 def function(self,name,ns):
  node=next(x for x in TREE.body if isinstance(x,ast.FunctionDef) and x.name==name)
  node=ast.parse(ast.unparse(node)).body[0];node.decorator_list=[]
  exec(compile(ast.Module(body=[node],type_ignores=[]),'test','exec'),ns)
  return ns[name]
 def test_translation_and_cooking_context(self):
  api=Mock(return_value=(S(text=json.dumps({'prompt_english':PROMPT})),'test'))
  fn=self.function('_prompt_flux_ingles',{'n':S(generar_con_respaldo=api),'cliente_gemini':lambda:None,'_flux':f})
  result=fn('Menestra de lenteja con arroz','Lenteja, arroz, tomate',('Cocinar el refrito',),'Ecuatoriana')
  self.assertEqual(result,PROMPT)
  self.assertIn('Cocinar el refrito',api.call_args.args[1])
  self.assertIn('ENTIRELY IN ENGLISH',api.call_args.args[1])
 def test_only_english_prompt_reaches_flux(self):
  with patch.object(f.requests,'get',return_value=Response()) as get:
   f.generar('Menestra de lenteja con arroz','Lenteja, tomate',KEY,prompt_ingles=PROMPT)
  actual=unquote(get.call_args.args[0].removeprefix(f.ENDPOINT))
  self.assertEqual(actual,PROMPT)
  self.assertNotIn('Menestra',actual)
 def test_empty_translation_fails_before_image_request(self):
  fn=self.function('_prompt_flux_ingles',{'n':S(generar_con_respaldo=lambda *a,**kw:(S(text='{}'),'test')),'cliente_gemini':lambda:None,'_flux':f})
  with self.assertRaises(f.ErrorImagen):fn('Arroz','arroz')
 def test_cache_gets_translated_prompt(self):
  cache=Mock(return_value=b'image')
  fn=self.function('crear_imagen',{'_flux':f,'secreto':lambda k:KEY if k=='POLLINATIONS_API_KEY' else None,'_prompt_flux_ingles':lambda *a:PROMPT,'_crear_imagen_cache':cache})
  self.assertEqual(fn('Arroz','arroz'),b'image')
  self.assertEqual(cache.call_args.args[-1],PROMPT)
if __name__=='__main__':unittest.main()
