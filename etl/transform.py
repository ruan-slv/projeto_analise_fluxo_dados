import numpy as np
import pandas as pd
from pathlib import Path

caminho_pasta_data_bruto = Path(__file__).resolve().parent.parent / "data/bruto"
caminho_pasta_data_transformado = Path(__file__).resolve().parent.parent / "data/transformado"

ddate = pd.date_range(start="2006-01-01", end="2026-12-31")
dimensao_data = pd.DataFrame({
    "DateID": ddate.strftime("%Y%m%d").astype(int),
    "FullDate": ddate.strftime("%Y-%m-%d"),
    "Day": ddate.day,
    "Month": ddate.month,
    "Year": ddate.year,
    "Semester": np.where(ddate.month <= 6, 1, 2)
})
dimensao_data.to_csv(caminho_pasta_data_transformado / "ddate.csv", index=False)

dtime = pd.date_range(start="00:00:00", end="23:59:59", freq="min")
dimensao_time = pd.DataFrame({
    "TimeID": dtime.strftime("%H%M").astype(int),
    "FullTime": dtime.strftime("%H:%M:%S"),
    "Hour": dtime.hour,
    "Minute": dtime.minute,
    "Second": 0
})
dimensao_time.to_csv(caminho_pasta_data_transformado / "dtime.csv", index=False)

ddepartment_raw = pd.read_csv(caminho_pasta_data_bruto / "department.csv")
demployee_raw = pd.read_csv(caminho_pasta_data_bruto / "employee.csv")
demployee_department_history = pd.read_csv(caminho_pasta_data_bruto / "employee_department_history.csv")
demployee_pay_history = pd.read_csv(caminho_pasta_data_bruto / "employee_pay_history.csv")
djobcandidate_raw = pd.read_csv(caminho_pasta_data_bruto / "job_candidate.csv")
dshift_raw = pd.read_csv(caminho_pasta_data_bruto / "shift.csv")

ddepartment = ddepartment_raw[['DepartmentID', 'Name', 'GroupName']].copy()
ddepartment.to_csv(caminho_pasta_data_transformado / "ddepartment.csv", index=False)

demployee = demployee_raw[[
    'BusinessEntityID', 'NationalIDNumber', 'LoginID', 'OrganizationNode',
    'OrganizationLevel', 'JobTitle', 'MaritalStatus', 'Gender',
    'BirthDate', 'HireDate', 'SalariedFlag', 'CurrentFlag'
]].copy()
demployee.columns = [
    'EmployeeID', 'NationalIDNumber', 'LoginID', 'OrganizationNode',
    'OrganizationLevel', 'JobTitle', 'MaritalStatus', 'Gender',
    'BirthDate', 'HireDate', 'SalariedFlag', 'CurrentFlag'
]
demployee['SalariedFlag'] = demployee['SalariedFlag'].astype(int)
demployee['CurrentFlag'] = demployee['CurrentFlag'].astype(int)
demployee['OrganizationLevel'] = demployee['OrganizationLevel'].astype('Int64')
demployee.to_csv(caminho_pasta_data_transformado / "demployee.csv", index=False)

dshift = dshift_raw[['ShiftID', 'Name', 'StartTime', 'EndTime']].copy()
dshift.to_csv(caminho_pasta_data_transformado / "dshift.csv", index=False)

djob_candidate = djobcandidate_raw[['JobCandidateID', 'Resume']].copy()
djob_candidate.to_csv(caminho_pasta_data_transformado / "djob_candidate.csv", index=False)

demployee_pay_history['PayHistoryID'] = range(1, len(demployee_pay_history) + 1)
dpay_history = demployee_pay_history[['PayHistoryID', 'PayFrequency']].copy()
dpay_history.columns = ['PayHistoryID', 'PayFrequence']
dpay_history.to_csv(caminho_pasta_data_transformado / "dpay_history.csv", index=False)

fhr = demployee_department_history.merge(demployee_pay_history, on='BusinessEntityID', how='left')
fhr = fhr.merge(demployee_raw[['BusinessEntityID', 'VacationHours', 'SickLeaveHours']], on='BusinessEntityID', how='left')
fhr = fhr.merge(djobcandidate_raw[['JobCandidateID', 'BusinessEntityID']], on='BusinessEntityID', how='left')

fhr['DateID'] = pd.to_datetime(fhr['StartDate']).dt.strftime('%Y%m%d').astype(int)

fhuman_resources = pd.DataFrame({
    'FHumanResources': range(1, len(fhr) + 1),
    'DateID': fhr['DateID'],
    'TimeID': 1200,
    'DepartmentID': fhr['DepartmentID'],
    'EmployeeID': fhr['BusinessEntityID'],
    'PayHistoryID': fhr['PayHistoryID'],
    'ShiftID': fhr['ShiftID'],
    'JobCandidateID': fhr['JobCandidateID'].astype('Int64'),
    'Rate': fhr['Rate'],
    'VacationHours': fhr['VacationHours'],
    'SickLeaveHours': fhr['SickLeaveHours']
})
fhuman_resources.to_csv(caminho_pasta_data_transformado / "fhuman_resources.csv", index=False)

print("Transform incremental concluído: dimensões e fatos salvos em CSV.")
