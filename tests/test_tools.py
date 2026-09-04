from backend.tools.code_tool import run_code
from backend.tools.document_tool import generate_docx, generate_pptx, edit_spreadsheet
from backend.tools.file_tool import write_file, read_file

def test_code_sandbox_execution():
    code = "x = 10\ny = 20\nprint(f'Sum: {x+y}')"
    res = run_code(code)
    assert res["success"] is True
    assert "Sum: 30" in res["stdout"]

def test_file_read_write():
    write_res = write_file("test_output.txt", "Test content for sovereign backend")
    assert write_res["success"] is True

    read_res = read_file(write_res["file_path"])
    assert read_res["success"] is True
    assert "Test content for sovereign backend" in read_res["content"]

def test_docx_generation():
    res = generate_docx("Test Title", "Sample body paragraph.", "Test_Note.docx")
    assert res["success"] is True

def test_spreadsheet_generation():
    rows = [["Tag", "Val"], ["P-101", "100"]]
    res = edit_spreadsheet(rows, "Test_Calc.xlsx")
    assert res["success"] is True
