"""Version gates for the newly verified geometry workflow, not all legacy APIs."""
import re


def geometry_version_policy(version):
    match = re.search(r'(?:COMSOL Multiphysics\s+)?(\d+\.\d+)(?:\D|$)', str(version))
    actual = match.group(1) if match else None
    supported = actual == '6.4'
    return {'status': 'PASS' if supported else 'BLOCKED',
            'version_status': 'MATCH_6_4' if supported else 'VERSION_MISMATCH',
            'actual_version': str(version),
            'manual': 'https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_api_geom.48.047.html',
            'reason': None if supported else 'Re-anchor geometry/selection/CAD methods to the actual installed-version manual before using this workflow.'}
