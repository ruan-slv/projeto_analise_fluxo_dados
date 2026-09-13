"""
import csv

import numpy as np
import pandas as pd

caminho_pasta_data = "../data/"

ddate = pd.date_range(start="2006-01-01", end="2026-12-31")
dimensao_data = pd.DataFrame({
    "dateid": ddate.strftime("%Y%m%d"),
    "fulldate": ddate.strftime("%Y-%m-%d"),
    "day": ddate.day,
    "month": ddate.month,
    "year": ddate.year,
    "semester": np.where(ddate.month <= 6, 1, 2)
})

dtime = pd.date_range(start="00:00:00", end="23:59:59", freq="s")
dimensao_time = pd.DataFrame({
    "timeid": dtime.strftime("%H%M%S"),
    "fulltime": dtime.strftime("%H:%M:%S"),
    "hour": dtime.hour,
    "minute": dtime.minute,
    "second": dtime.second
})

print("--- Dimensão Data ---")
print(dimensao_data.head())
print(dimensao_data.info())

print("\n--- Dimensão Tempo ---")
print(dimensao_time.head())

ddepartment = pd.read_csv(caminho_pasta_data + "department.csv")
demployee = pd.read_csv(caminho_pasta_data + "employee.csv")
demployee_department_history = pd.read_csv(caminho_pasta_data + "employee_department_history.csv")
demployee_pay_history = pd.read_csv(caminho_pasta_data + "employee_pay_history.csv")
djobcandidate = pd.read_csv(caminho_pasta_data + "job_candidate.csv")
dshift = pd.read_csv(caminho_pasta_data + "shift.csv")
"""


"""
import numpy as np
import pandas as pd

caminho_pasta_data = "../data/"

ddate = pd.date_range(start="2006-01-01", end="2026-12-31")
dimensao_data = pd.DataFrame({
    "dateid": ddate.strftime("%Y%m%d"),
    "fulldate": ddate.strftime("%Y-%m-%d"),
    "day": ddate.day,
    "month": ddate.month,
    "year": ddate.year,
    "semester": np.where(ddate.month <= 6, 1, 2)
})

dtime = pd.date_range(start="00:00:00", end="23:59:59", freq="s")
dimensao_time = pd.DataFrame({
    "timeid": dtime.strftime("%H%M%S"),
    "fulltime": dtime.strftime("%H:%M:%S"),
    "hour": dtime.hour,
    "minute": dtime.minute,
    "second": dtime.second
})

ddepartment_raw = pd.read_csv(caminho_pasta_data + "department.csv")
demployee_raw = pd.read_csv(caminho_pasta_data + "employee.csv")
demployee_department_history = pd.read_csv(caminho_pasta_data + "employee_department_history.csv")
demployee_pay_history = pd.read_csv(caminho_pasta_data + "employee_pay_history.csv")
djobcandidate_raw = pd.read_csv(caminho_pasta_data + "job_candidate.csv")
dshift_raw = pd.read_csv(caminho_pasta_data + "shift.csv")

ddepartment = ddepartment_raw[['DepartmentID', 'Name', 'GroupName']].copy()
ddepartment.columns = ['departmentid', 'name', 'groupname']

demployee = demployee_raw[[
    'BusinessEntityID', 'NationalIDNumber', 'LoginID', 'OrganizationNode',
    'OrganizationLevel', 'JobTitle', 'MaritalStatus', 'Gender',
    'BirthDate', 'HireDate', 'SalariedFlag', 'CurrentFlag'
]].copy()
demployee.columns = [
    'employeeid', 'nationalidnumber', 'loginid', 'organizationnode',
    'organizationlevel', 'jobtitle', 'maritalstatus', 'gender',
    'birthdate', 'hiredate', 'salariedflag', 'currentflag'
]

dshift = dshift_raw[['ShiftID', 'Name', 'StartTime', 'EndTime']].copy()
dshift.columns = ['shiftid', 'name', 'starttime', 'endtime']

djob_candidate = djobcandidate_raw[['JobCandidateID', 'Resume']].copy()
djob_candidate.columns = ['jobcandidateid', 'resume']

demployee_pay_history['payhistoryid'] = range(1, len(demployee_pay_history) + 1)
dpay_history = demployee_pay_history[['payhistoryid', 'PayFrequency']].copy()
dpay_history.columns = ['payhistoryid', 'payfrequence']

fhr = demployee_department_history.merge(demployee_pay_history, on='BusinessEntityID', how='left')
fhr = fhr.merge(demployee_raw[['BusinessEntityID', 'VacationHours', 'SickLeaveHours']], on='BusinessEntityID', how='left')
fhr = fhr.merge(djobcandidate_raw[['JobCandidateID', 'BusinessEntityID']], on='BusinessEntityID', how='left')

fhr['fulldate'] = pd.to_datetime(fhr['StartDate']).dt.strftime('%Y%m%d')
fhr['dateid'] = fhr['fulldate'].astype(int)

fhuman_resources = pd.DataFrame({
    'fhuman_resources': range(1, len(fhr) + 1),
    'dateid': fhr['dateid'],
    'timeid': 120000,  # ID padrão para horário (12:00:00)
    'departmentid': fhr['DepartmentID'],
    'employeeid': fhr['BusinessEntityID'],
    'payhistoryid': fhr['payhistoryid'],
    'shiftid': fhr['ShiftID'],
    'jobcandidateid': fhr['JobCandidateID'].fillna(0).astype(int),
    'rate': fhr['Rate'],
    'vacationhours': fhr['VacationHours'],
    'sickleavehours': fhr['SickLeaveHours']
})

print("Todas as tabelas dimensões e fatos foram processadas com sucesso.")

"""

import csv
import numpy as np
import pandas as pd

caminho_pasta_data = "../data/"

ddate = pd.date_range(start="2006-01-01", end="2026-12-31")
dimensao_data = pd.DataFrame({
    "fulldate": ddate.strftime("%Y-%m-%d"),
    "day": ddate.day,
    "month": ddate.month,
    "year": ddate.year,
    "semester": np.where(ddate.month <= 6, 1, 2)
})

dtime = pd.date_range(start="00:00:00", end="23:59:59", freq="s")
dimensao_time = pd.DataFrame({
    "hour": dtime.hour,
    "minute": dtime.minute,
    "second": dtime.second
})

ddepartment_raw = pd.read_csv(caminho_pasta_data + "department.csv")
demployee_raw = pd.read_csv(caminho_pasta_data + "employee.csv")
demployee_department_history = pd.read_csv(caminho_pasta_data + "employee_department_history.csv")
demployee_pay_history = pd.read_csv(caminho_pasta_data + "employee_pay_history.csv")
djobcandidate_raw = pd.read_csv(caminho_pasta_data + "job_candidate.csv")
dshift_raw = pd.read_csv(caminho_pasta_data + "shift.csv")

ddepartment = ddepartment_raw[['DepartmentID', 'Name', 'GroupName']].copy()
ddepartment.columns = ['departmentid', 'name', 'groupname']

demployee = demployee_raw[[
    'BusinessEntityID', 'NationalIDNumber', 'LoginID', 'OrganizationNode',
    'OrganizationLevel', 'JobTitle', 'MaritalStatus', 'Gender',
    'BirthDate', 'HireDate', 'SalariedFlag', 'CurrentFlag'
]].copy()
demployee.columns = [
    'employeeid', 'nationalidnumber', 'loginid', 'organizationnode',
    'organizationlevel', 'jobtitle', 'maritalstatus', 'gender',
    'birthdate', 'hiredate', 'salariedflag', 'currentflag'
]

dshift = dshift_raw[['ShiftID', 'Name', 'StartTime', 'EndTime']].copy()
dshift.columns = ['shiftid', 'name', 'starttime', 'endtime']

djob_candidate = djobcandidate_raw[['JobCandidateID', 'Resume']].copy()
djob_candidate.columns = ['jobcandidateid', 'resume']

demployee_pay_history['payhistoryid'] = range(1, len(demployee_pay_history) + 1)
dpay_history = demployee_pay_history[['payhistoryid', 'PayFrequency']].copy()
dpay_history.columns = ['payhistoryid', 'payfrequence']

fhr = demployee_department_history.merge(demployee_pay_history, on='BusinessEntityID', how='left')
fhr = fhr.merge(demployee_raw[['BusinessEntityID', 'VacationHours', 'SickLeaveHours']], on='BusinessEntityID', how='left')
fhr = fhr.merge(djobcandidate_raw[['JobCandidateID', 'BusinessEntityID']], on='BusinessEntityID', how='left')
fhr['start_date_formatted'] = pd.to_datetime(fhr['StartDate']).dt.strftime('%Y-%m-%d')

fhuman_resources = pd.DataFrame({
    'start_date_formatted': fhr['start_date_formatted'],
    'departmentid': fhr['DepartmentID'],
    'employeeid': fhr['BusinessEntityID'],
    'payhistoryid': fhr['payhistoryid'],
    'shiftid': fhr['ShiftID'],
    'jobcandidateid': fhr['JobCandidateID'].replace({np.nan: None}),
    'rate': fhr['Rate'],
    'vacationhours': fhr['VacationHours'],
    'sickleavehours': fhr['SickLeaveHours']
})

print("Todas as tabelas dimensões e fatos foram processadas com sucesso e estão em conformidade com o DW.")
