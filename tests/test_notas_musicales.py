import unittest
import numpy as np
from audio.notas_musicales import detectar_notas, emparejar, analizar_notas


def note(i,start,end,midi):
 return dict(id=i,inicio_s=start,fin_s=end,midi=midi)

class MusicalTests(unittest.TestCase):
 def test_vibrato_and_short_transition_have_stable_center(self):
  t=np.arange(0,2,.01);m=69+.5*np.sin(2*np.pi*5*t)
  notes=detectar_notas(t,440*2**((m-69)/12),0,2,'r')
  self.assertEqual(len(notes),1);self.assertAlmostEqual(notes[0]['midi'],69,delta=.1)
 def test_semitone_change_creates_distinct_notes(self):
  t=np.arange(0,2,.01);f=np.where(t<1,440,440*2**(1/12))
  notes=detectar_notas(t,f,0,2,'r')
  self.assertEqual(len(notes),2)
  self.assertAlmostEqual(notes[1]['midi']-notes[0]['midi'],1,places=5)
 def test_pairing_ignores_pitch_and_keeps_octave_errors(self):
  refs=[note('r',0,1,69)]
  users=[note('wrong',0,1,81),note('right',.2,1,69)]
  paired=emparejar(refs,users)
  self.assertEqual(paired[0][1]['id'],'wrong')
 def test_no_reuse_and_no_large_temporal_warp(self):
  refs=[note('r1',0,1,69),note('r2',1,2,69)]
  self.assertEqual(len(emparejar(refs,[note('u',0,2,69)])),1)
  self.assertEqual(emparejar([refs[0]],[note('late',.4,1.4,69)]),[])
 def test_missing_notes_reduce_coverage_not_count_as_success(self):
  t=np.arange(0,4,.01);f=np.where(t<2,440,660.)
  u=f.copy();u[t>=2]=0
  report,_=analizar_notas(t,f,t,u,[dict(id='f0001',inicio_s=0,fin_s=4)])
  self.assertEqual(report['metricas']['notas_referencia'],2)
  self.assertEqual(report['metricas']['notas_comparadas'],1)
  self.assertEqual(report['metricas']['cobertura_notas_pct'],50)
  self.assertEqual(report['metricas']['porcentaje_50'],100)
 def test_octaves_are_counted_as_wrong_without_correction(self):
  t=np.arange(0,2,.01);f=np.full(len(t),440.)
  report,_=analizar_notas(t,f,t,f*2,[dict(id='f0001',inicio_s=0,fin_s=2)])
  self.assertEqual(report['metricas']['porcentaje_100'],0)
  self.assertAlmostEqual(report['notas'][0]['error_cents'],1200)
 def test_global_totals_equal_fragment_counts(self):
  t=np.arange(0,4,.01);f=np.where(t<2,440,660.)
  report,parts=analizar_notas(t,f,t,f,[dict(id='f0001',inicio_s=0,fin_s=2),dict(id='f0002',inicio_s=2,fin_s=4)])
  self.assertEqual(report['metricas']['notas_comparadas'],sum(p['metricas']['notas_comparadas'] for p in parts.values()))
  ids=[n['usuario']['id'] for n in report['notas'] if n['usuario']]
  self.assertEqual(len(ids),len(set(ids)))
 def test_empty_and_too_short_notes_have_no_percentage(self):
  report,_=analizar_notas([],[],[],[],[dict(id='f0001',inicio_s=0,fin_s=2)])
  self.assertIsNone(report['metricas']['porcentaje_50'])
  self.assertEqual(detectar_notas([0,.01,.02],[440]*3,0,.04,'r'),[])

if __name__=='__main__':unittest.main()
