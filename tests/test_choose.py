import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]))
from router.choose import choose
class T(unittest.TestCase):
 def test_budget(self):
  c={'models':[{'id':'nano-banana-2','pricing':{'effective':{'2k':'.025'}}}]}
  self.assertEqual(choose(c,1024,1024,'medium',.03)['model'],'nano-banana-2')
if __name__=='__main__':unittest.main()
