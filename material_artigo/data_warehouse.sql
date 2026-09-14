CREATE TABLE dw_metadata (
    id serial primary key,
    table_name varchar(100) not null,
    last_load_date timestamp not null,
    records_processed int default 0
);

select * from dw_metadata;

CREATE TABLE ddate(
    DateID serial primary key,
    FullDate date not null,
    Day smallint not null,
    Month smallint not null,
    Year smallint not null,
    Semester smallint not null
);

select * from ddate;

CREATE TABLE dtime(
    TimeID serial primary key,
    FullTime time not null,
    Hour smallint not null,
    Minute smallint not null,
    Second smallint not null
);

select * from dtime;

CREATE TABLE dshift(
    ShiftID int primary key,
    Name varchar(100) not null,
    StartTime time not null,
    EndTime time
);

select * from dshift;

CREATE TABLE ddepartment(
    DepartmentID int primary key,
    Name varchar(100) not null,
    GroupName varchar(100) not null
);

select * from ddepartment;

CREATE TABLE djob_candidate(
    JobCandidateID int primary key,
    Resume text
);

select * from djob_candidate;

CREATE TABLE dpay_history(
    PayHistoryID int primary key,
    PayFrequence smallint not null
);

select * from dpay_history;

CREATE TABLE demployee(
    EmployeeID int primary key,
    NationalIDNumber varchar(15) not null,
    LoginID varchar(256) not null,
    OrganizationNode varchar(892),
    OrganizationLevel smallint,
    JobTitle varchar(50) not null,
    MaritalStatus char(1) not null,
    Gender char(1) not null,
    BirthDate date not null,
    HireDate date not null,
    SalariedFlag smallint check(SalariedFlag in (0,1)),
    CurrentFlag smallint check(CurrentFlag in (0,1))
);

select * from demployee;

CREATE TABLE fhuman_resources(
    FHumanResources serial primary key,
    DateID int not null REFERENCES ddate(DateID),
    TimeID int not null REFERENCES dtime(TimeID),
    DepartmentID int not null REFERENCES ddepartment(DepartmentID),
    EmployeeID int not null REFERENCES demployee(EmployeeID),
    PayHistoryID int not null REFERENCES dpay_history(PayHistoryID),
    ShiftID int not null REFERENCES dshift(ShiftID),
    JobCandidateID int REFERENCES djob_candidate(JobCandidateID),
    Rate numeric(15,2) not null,
    VacationHours smallint not null,
    SickLeaveHours smallint not null
);

select * from fhuman_resources;
