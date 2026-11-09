#!/usr/bin/env python3
# rcm_refresh.py — daily builder/reproducer for the NPHIES RCM Consistency Audit (source: Cure+).
# Runs the build steps in order against the staged raw/ inputs and rebuilds every JSON, then the
# Excel workbook and the HTML dashboard. Order matters (later steps read earlier JSON):
#   build_data -> build_vf -> build_pbm -> build_sfda -> build_dxappr -> build_xlsx -> build_html
#
# raw/ inputs expected:
#   check12.md, check3.md, check4.md, check5.md, agg.json           (build_data / build5)
#   vitals_00..NN.md                                                (build_vf)
#   pbm.md                                                          (build_pbm)
#   sfda_ref.json, services_inventory.csv, sfda_invoiced.md         (build_sfda)
#   drug_catalog.csv, dxappr_ep_0000..NNNN.md                       (build_dxappr)
#
# All build_*.py modules + dxappr_rules.py must sit beside this file (they ship in
# NPHIES_RCM_Audit_project.zip). This orchestrator runs them exactly as the interactive build did,
# so a clean run reproduces the published dashboard + workbook identically.
import runpy, importlib, sys, os

HERE = os.path.dirname(os.path.abspath(__file__)) or '.'
os.chdir(HERE)
sys.path.insert(0, HERE)

STEPS_SCRIPT = ['build_data.py', 'build_vf.py', 'build_pbm.py', 'build_sfda.py']
# build_dxappr is function-based (build()); run it explicitly between sfda and xlsx.
STEPS_SCRIPT_TAIL = ['build_xlsx.py', 'build_html.py']


def run_script(name):
    if not os.path.exists(name):
        print('SKIP (missing):', name); return
    print('=== run', name, '===')
    runpy.run_path(name, run_name='__main__')


for s in STEPS_SCRIPT:
    run_script(s)

# diagnosis appropriateness (needs raw/drug_catalog.csv + raw/dxappr_ep_*.md)
if os.path.exists('build_dxappr.py') and os.path.exists('raw/drug_catalog.csv'):
    print('=== run build_dxappr.build() ===')
    import build_dxappr
    importlib.reload(build_dxappr)
    build_dxappr.build()
else:
    print('SKIP build_dxappr (missing build_dxappr.py or raw/drug_catalog.csv) — appropriateness tabs will be empty this run')

# drug-drug interactions (reuses the appropriateness episode data + drug_catalog)
if os.path.exists('build_ddi.py') and os.path.exists('raw/drug_catalog.csv'):
    print('=== run build_ddi.build() ===')
    import build_ddi
    importlib.reload(build_ddi)
    build_ddi.build()
else:
    print('SKIP build_ddi — interaction tab will be empty this run')

# MDS (Minimum Data Set) compliance — from staged NPHIES claim pulls
if os.path.exists('build_mds.py') and os.path.exists('raw/mds_coding.md'):
    print('=== run build_mds.build() ===')
    import build_mds
    importlib.reload(build_mds)
    build_mds.build()
else:
    print('SKIP build_mds (missing build_mds.py or raw/mds_coding.md) — MDS tab will be empty this run')

for s in STEPS_SCRIPT_TAIL:
    run_script(s)

print('rcm_refresh complete — rebuilt audit_data.json, vitals.json, pbm.json, sfda.json, dxappr.json, ddi.json, mds.json, NPHIES_RCM_Audit.xlsx, rcm_dashboard.html')
