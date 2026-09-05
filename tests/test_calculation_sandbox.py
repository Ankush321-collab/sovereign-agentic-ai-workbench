import pytest
from backend.tools.code_tool import run_code

def test_barlow_calculation_sandbox():
    """TDD Seam: Verify Barlow formula calculation inside isolated sandbox."""
    calc_code = (
        "import math\n"
        "pressure_psi = 142.5\n"
        "diameter_inch = 12.4\n"
        "allowable_stress_psi = 16000.0\n"
        "joint_efficiency = 1.0\n"
        "corrosion_allowance_inch = 0.08\n"
        "t_design = (pressure_psi * diameter_inch) / (2 * (allowable_stress_psi * joint_efficiency + pressure_psi * 0.4))\n"
        "t_retire = t_design + corrosion_allowance_inch\n"
        "measured_thickness_inch = 0.1496\n"
        "margin_inch = measured_thickness_inch - t_retire\n"
        "passed = margin_inch >= 0\n"
        "print(f'DESIGN_THICKNESS={t_design:.4f}')\n"
        "print(f'RETIRE_THICKNESS={t_retire:.4f}')\n"
        "print(f'SAFETY_PASSED={passed}')\n"
    )

    result = run_code(code=calc_code, language="python")

    assert result["success"] is True, f"Execution failed: {result}"
    stdout = result["stdout"]
    assert "DESIGN_THICKNESS=" in stdout
    assert "RETIRE_THICKNESS=" in stdout
    assert "SAFETY_PASSED=" in stdout
