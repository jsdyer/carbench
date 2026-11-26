import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from refresh import parse_csv
class ImportTests(unittest.TestCase):
 def test_bom_and_zero_mixed_mode(self):
  data='\ufeffModel year,Make,Model,Vehicle class,Fuel type 2,Combined (L/100 km),Combined Le/100 km\n2026,Test,One,Compact,X,6.2,2.7 ([23.2 kWh + 0.1 L]/100 km)\n'.encode()
  row=parse_csv(data,'plugin',0)[0];self.assertEqual(row['electric'],23.2);self.assertEqual(row['modeFuel'],.1);self.assertEqual(row['combined'],6.2)
 def test_invalid_html_and_missing_consumption_rejected(self):
  with self.assertRaises(ValueError):parse_csv(b'<html>error</html>','fuel',0)
  with self.assertRaises(ValueError):parse_csv(b'Model year,Make,Model,Vehicle class\n2026,Test,One,Compact\n','fuel',0)
 def test_variant_identity_changes_with_powertrain(self):
  a=b'Model year,Make,Model,Vehicle class,Fuel type,Combined (L/100 km)\n2026,Test,One,Compact,X,6\n2026,Test,One,Compact,Z,7\n';r=parse_csv(a,'fuel',0);self.assertNotEqual(r[0]['id'],r[1]['id'])
