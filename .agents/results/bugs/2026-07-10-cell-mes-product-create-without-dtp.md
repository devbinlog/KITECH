# Cell-MES Product Create Without DTP

## Symptom
- Creating a product without selecting a DT Project returned `422 Unprocessable Entity`.
- The browser alert displayed `생성 실패: [object Object]`.

## Root Cause
- The failing product name was `드릴 지그 플레이트(cell1)`.
- DT Project is optional in `ProductCreate`, but `validate_safe_name` did not allow parentheses.
- FastAPI returned a validation detail array, and the frontend interpolated that object directly into the alert.

## Fix
- Allowed parentheses in MES safe name validation.
- Added a regression test for creating a product with `dt_project: null` and a parenthesized product name.
- Updated the product page to use the common API error formatter so validation arrays render as readable messages.

## Verification
- `uv run pytest tests/test_api/test_masters.py::TestProductCreate`
- `node node_modules/typescript/bin/tsc --noEmit`
