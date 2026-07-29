select distinct(c.subjid) from IE2 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid and b.sysbp>= 130 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=30 and  c.LBORRES <=75 ) and c.LBORRES <>''

256

157

121

89

15

select * from IE2


select distinct(c.subjid) from IE1 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid and b.sysbp>= 130 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=30 and  c.LBORRES <=75 ) and c.LBORRES <>''

select distinct(c.subjid) from IE1 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=60 and  c.LBORRES <=75 ) and c.LBORRES <>''


246  84

select * from board_t
SELECT * FROM board_t where UACR_txt is not null

select distinct(subjid) from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE1 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid and b.sysbp>= 130 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=30 and  c.LBORRES <=75 ) and c.LBORRES <>''
) and ((jc_type ='UACR' and jc_cnt >= 200 and jc_cnt < 5000)  
or (jc_type ='UPCR' and jc_cnt >= 500 AND jc_cnt < 8000)
or (jc_type ='24H' and jc_cnt >= 500 AND jc_cnt < 8000))

N7 64  N8 42
N5 186 N6 97
N4 49  N3 14
N1 65  N2 27
select distinct(subjid) from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE2 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=75 and  c.LBORRES <=90 ) and c.LBORRES <>''
) and ((jc_type ='UACR' and jc_cnt >= 500 and jc_cnt< 5000) 
or ( jc_type ='UPCR' and jc_cnt >= 1000 AND jc_cnt < 8000)
or (jc_type ='24H' and jc_cnt >= 1000 AND jc_cnt < 8000))

select distinct(subjid) from LBCHEM
where SUBJID in(
SELECT DISTINCT(subjid)
FROM CM 
WHERE 
    (CM.CMTRT LIKE '%普利%'
    OR CM.CMTRT LIKE '%利酮%'
    OR CM.CMTRT LIKE '%沙坦%' 
    OR CM.CMTRT LIKE '%列净%'
    OR CM.CMTRT LIKE '%螺内酯%') 
    AND CMONGO ='1' 
    AND subjid IN (
    select distinct(subjid) from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE1 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=60 and  c.LBORRES <=75 ) and c.LBORRES <>''
) and ((jc_type ='UACR' and jc_cnt >= 200 and jc_cnt < 5000)  
or (jc_type ='UPCR' and jc_cnt >= 1500 AND jc_cnt < 8000)
or (jc_type ='24H' and jc_cnt >= 1500 AND jc_cnt < 8000))
    
    )) and LBTEST2 = 20 and LBORRES >= 3.0  and LBORRES >= 4.8
    
    
  N1 175  
  N2 54
    
    select distinct(subjid) from LBCHEM
where SUBJID in(
SELECT DISTINCT(subjid)
FROM CM 
WHERE 
    (CM.CMTRT LIKE '%普利%'
    OR CM.CMTRT LIKE '%利酮%'
    OR CM.CMTRT LIKE '%沙坦%' 
    OR CM.CMTRT LIKE '%列净%'
    OR CM.CMTRT LIKE '%螺内酯%') 
    AND CMONGO ='1' 
    AND subjid IN (
    select distinct(subjid) from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE1 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid and b.sysbp>= 130 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=30 and  c.LBORRES <=75 ) and c.LBORRES <>''
) and ((jc_type ='UACR' and jc_cnt >= 700 and jc_cnt < 5000)  
or (jc_type ='UPCR' and jc_cnt >= 500 AND jc_cnt < 8000)
or (jc_type ='24H' and jc_cnt >= 500 AND jc_cnt < 8000))
    
    )) and LBTEST2 = 20 and LBORRES >= 3.0  and LBORRES >= 4.8
    
---------------------------------------

select subjid,jc_cnt,jc_type from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE2 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid and b.sysbp>= 130 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=75 and  c.LBORRES <=90 ) and c.LBORRES <>''
) and ((jc_type ='UACR' and jc_cnt>=200 and jc_cnt< 500)  
or (jc_type ='UPCR' and jc_cnt >= 500 AND jc_cnt < 1000)
or (jc_type ='24H' and jc_cnt >= 500 AND jc_cnt < 1000))

select subjid,jc_cnt,jc_type from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE2 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid and b.sysbp>= 130 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=30 and  c.LBORRES <=75 ) and c.LBORRES <>''
) and jc_type ='UPCR' and jc_cnt >= 500 AND jc_cnt < 1000

select subjid,jc_cnt,jc_type from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE2 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid and b.sysbp>= 130 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=30 and  c.LBORRES <=75 ) and c.LBORRES <>''
) and jc_type ='24H' and jc_cnt >= 500 AND jc_cnt < 1000

----------------------------------------------------------------


N8 48 N7 19
N6 87 N5 80
N3 12 N4 34
N1 32 N2 22
select * from DM where subjid in ('E130321026',
'E130441001')


select * from DM where subjid in ('E130321030',
'E130401034')

select distinct(subjid),jc_cnt,jc_type from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE2 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid and b.sysbp>= 130 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=20 and  c.LBORRES < 30 ) and c.LBORRES <>''
) 


N7 19 N8 40 
N5 80 N6 86
N4 32 N3 14 
N1 32 N2 23

select subjid,jc_cnt,jc_type from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE2 as a, DM as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid and b.AGE < 60
) and ((jc_type ='UACR' and jc_cnt >=5000) 
or ( jc_type ='UPCR' and jc_cnt > 8000)
or (jc_type ='24H' and jc_cnt > 8000))

select subjid,jc_cnt,jc_type from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE2 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=60 and  c.LBORRES <=75 ) and c.LBORRES <>''
) and ((jc_type ='UACR' and jc_cnt>=30 and jc_cnt< 200) or 
(jc_type ='UPCR' and jc_cnt >= 150 AND jc_cnt < 370)
or (jc_type ='24H' and jc_cnt >= 150 AND jc_cnt < 370))

select distinct(subjid),jc_cnt,jc_type from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE2 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=75 and  c.LBORRES < 90 ) and c.LBORRES <>''
) 
and ((jc_type ='UACR' and jc_cnt >= 500 and jc_cnt< 5000) 
or ( jc_type ='UPCR' and jc_cnt >= 1000 AND jc_cnt < 8000)
or (jc_type ='24H' and jc_cnt >= 1000 AND jc_cnt < 8000))

select subjid,jc_cnt,jc_type from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE2 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid and b.sysbp>= 130 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=30 and  c.LBORRES <=75 ) and c.LBORRES <>''
) and (jc_type ='UACR' and jc_cnt>=500 and jc_cnt< 5000) 
or ( jc_type ='UPCR' and jc_cnt >= 1000 AND jc_cnt < 8000)
or (jc_type ='24H' and jc_cnt >= 1000 AND jc_cnt < 8000)


select subjid,jc_cnt,jc_type from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE2 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid and b.sysbp>= 130 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=30 and  c.LBORRES <=75 ) and c.LBORRES <>''
) and jc_type ='UPCR' and jc_cnt >= 1000 AND jc_cnt < 8000

select subjid,jc_cnt,jc_type from jc_t_td2 where subjid in(
select distinct(c.subjid) from IE2 as a, VS as b ,LBCKD as c 
where a.SUBJID = b.subjid and a.SUBJID=c.subjid and b.sysbp>= 130 
and c.LBTEST3_TXT like '%eGFR%' and ( c.LBORRES >=30 and  c.LBORRES <=75 ) and c.LBORRES <>''
) and jc_type ='24H' and jc_cnt >= 1000 AND jc_cnt < 8000



-------------------------------------

SELECT DISTINCT(subjid)
FROM CM 
WHERE 
    (CM.CMTRT LIKE '%普利%'
    OR CM.CMTRT LIKE '%利酮%'
    OR CM.CMTRT LIKE '%沙坦%' 
    OR CM.CMTRT LIKE '%列净%'
    OR CM.CMTRT LIKE '%螺内酯%') 
    AND CMONGO ='1' 
    AND subjid IN (
        SELECT subjid 
        FROM jc_t_td2 
        WHERE subjid IN (
            SELECT DISTINCT(c.subjid) 
            FROM IE2 AS a, VS AS b, LBCKD AS c 
            WHERE a.SUBJID = b.subjid 
                AND a.SUBJID = c.subjid 
                AND b.sysbp >= 130 
                AND c.LBTEST3_TXT LIKE '%eGFR%' 
                AND (c.LBORRES >= 30 AND c.LBORRES <= 75) 
                AND c.LBORRES <> ''
        ) 
        AND jc_type = 'UACR' 
        AND jc_cnt >= 500 
        AND jc_cnt < 5000
    )
    
    SELECT DISTINCT(subjid)
FROM CM 
WHERE 
    (CM.CMTRT LIKE '%普利%'
    OR CM.CMTRT LIKE '%利酮%'
    OR CM.CMTRT LIKE '%沙坦%' 
    OR CM.CMTRT LIKE '%列净%'
    OR CM.CMTRT LIKE '%螺内酯%') 
    AND CMONGO ='1' 
    AND subjid IN (
        SELECT subjid 
        FROM jc_t_td2 
        WHERE subjid IN (
            SELECT DISTINCT(c.subjid) 
            FROM IE2 AS a, VS AS b, LBCKD AS c 
            WHERE a.SUBJID = b.subjid 
                AND a.SUBJID = c.subjid 
                AND b.sysbp >= 130 
                AND c.LBTEST3_TXT LIKE '%eGFR%' 
                AND (c.LBORRES >= 30 AND c.LBORRES <= 75) 
                AND c.LBORRES <> ''
        ) 
        AND jc_type = 'UPCR' 
        AND jc_cnt >= 1000 
        AND jc_cnt < 8000
    )
    
    

--------------------------------

select * from LBCHEM 
where LBTEST2= 20 and LBORRES > 3.0 and LBORRES < 4.8
and subjid in(
SELECT DISTINCT(subjid)
FROM CM 
WHERE 
    (CM.CMTRT LIKE '%普利%'
    OR CM.CMTRT LIKE '%利酮%'
    OR CM.CMTRT LIKE '%沙坦%' 
    OR CM.CMTRT LIKE '%列净%'
    OR CM.CMTRT LIKE '%螺内酯%') 
    AND CMONGO ='1' 
    AND subjid IN (
        SELECT subjid 
        FROM jc_t_td2 
        WHERE subjid IN (
            SELECT DISTINCT(c.subjid) 
            FROM IE2 AS a, VS AS b, LBCKD AS c 
            WHERE a.SUBJID = b.subjid 
                AND a.SUBJID = c.subjid 
                AND b.sysbp >= 130 
                AND c.LBTEST3_TXT LIKE '%eGFR%' 
                AND (c.LBORRES >= 30 AND c.LBORRES <= 75) 
                AND c.LBORRES <> ''
        ) 
         AND jc_type = 'UPCR' 
        AND jc_cnt >= 1000 
        AND jc_cnt < 8000
    )
)



-------------------------------------


SELECT DISTINCT(subjid)
FROM CM 
WHERE 
    (CM.CMTRT LIKE '%普利%'
    OR CM.CMTRT LIKE '%利酮%'
    OR CM.CMTRT LIKE '%沙坦%' 
    OR CM.CMTRT LIKE '%列净%'
    OR CM.CMTRT LIKE '%螺内酯%') 
    AND CMONGO ='1' 
    
    
    
 select DISTINCT(a.subjid) from  IE2 as a ,CM as b where a.SUBJID=b.subjid and  
 (b.CMTRT LIKE '%普利%'
    OR b.CMTRT LIKE '%利酮%'
    OR b.CMTRT LIKE '%沙坦%' 
    OR b.CMTRT LIKE '%列净%'
    OR b.CMTRT LIKE '%螺内酯%') 
    AND b.CMONGO ='1' 


386

275

select count(*) from IE2

select * from jc_t_td2

select * from board_t where eGFR_txt is not null

B亚总人数 386

持续使用RASSI的 204



SELECT 
        count(a.subjid),DISTINCT(b.subjid),
        a.cohort,
        a.jc_type,
        CASE 
            WHEN jc_type = 'UACR' AND jc_cnt > 0 AND jc_cnt < 30 THEN '0-29'
            WHEN jc_type = 'UACR' AND jc_cnt >= 30 AND jc_cnt < 200 THEN '30-199'
            WHEN jc_type = 'UACR' AND jc_cnt >= 200 AND jc_cnt < 299 THEN '200-299'
            WHEN jc_type = 'UACR' AND jc_cnt >= 300 AND jc_cnt < 500 THEN '300-499'
            WHEN jc_type = 'UACR' AND jc_cnt >= 500 AND jc_cnt < 700 THEN '500-699'
            WHEN jc_type = 'UACR' AND jc_cnt >= 700 AND jc_cnt < 2000 THEN '700-1999'
            WHEN jc_type = 'UACR' AND jc_cnt >= 2000 AND jc_cnt < 5000 THEN '2000-4999'
            WHEN jc_type = 'UACR' AND jc_cnt >= 5000 THEN '>=5000'
            WHEN jc_type = 'UPCR' AND jc_cnt > 0 AND jc_cnt < 150 THEN '0-29'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 150 AND jc_cnt < 500 THEN '30-199'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 500 AND jc_cnt < 650 THEN '200-299'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 500 AND jc_cnt < 1000 THEN '300-499'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 1000 AND jc_cnt < 1500 THEN '500-699'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 1500 AND jc_cnt < 3500 THEN '700-1999'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 3500 AND jc_cnt < 8000 THEN '2000-4999'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 8000 THEN '>=5000'
            WHEN jc_type = '24H' AND jc_cnt > 0 AND jc_cnt < 150 THEN '0-29'
            WHEN jc_type = '24H' AND jc_cnt >= 150 AND jc_cnt < 500 THEN '30-199'
            WHEN jc_type = '24H' AND jc_cnt >= 500 AND jc_cnt < 650 THEN '200-299'
            WHEN jc_type = '24H' AND jc_cnt >= 500 AND jc_cnt < 1000 THEN '300-499'
            WHEN jc_type = '24H' AND jc_cnt >= 1000 AND jc_cnt < 1500 THEN '500-699'
            WHEN jc_type = '24H' AND jc_cnt >= 1500 AND jc_cnt < 3500 THEN '700-1999'
            WHEN jc_type = '24H' AND jc_cnt >= 3500 AND jc_cnt < 8000 THEN '2000-4999'
            WHEN jc_type = '24H' AND jc_cnt >= 8000 THEN '>=5000'
            WHEN jc_cnt = '0' OR jc_cnt IS NULL THEN '缺失'
        END AS AgeRange,
            FROM jc_t_td2 as a , CM as b
    WHERE a.subjid=b.subjid and a.jc_dt < DATE_SUB(CURDATE(), INTERVAL 4 WEEK) and a.cohort='B'
    and  (b.CMTRT LIKE '%普利%'
    OR b.CMTRT LIKE '%利酮%'
    OR b.CMTRT LIKE '%沙坦%' 
    OR b.CMTRT LIKE '%列净%'
    OR b.CMTRT LIKE '%螺内酯%') 
    AND b.CMONGO ='1' 
    GROUP BY  a.cohort, a.jc_type, AgeRange
    
    
    
    -----------------------------------------------------------
    
    
    SELECT 
    COUNT(DISTINCT a.subjid) AS unique_subjid_count,
    a.cohort,
    a.jc_type,
    CASE 
        WHEN jc_type = 'UACR' AND jc_cnt > 0 AND jc_cnt < 30 THEN '0-29'
        WHEN jc_type = 'UACR' AND jc_cnt >= 30 AND jc_cnt < 200 THEN '30-199'
        WHEN jc_type = 'UACR' AND jc_cnt >= 200 AND jc_cnt < 299 THEN '200-299'
        WHEN jc_type = 'UACR' AND jc_cnt >= 300 AND jc_cnt < 500 THEN '300-499'
        WHEN jc_type = 'UACR' AND jc_cnt >= 500 AND jc_cnt < 700 THEN '500-699'
        WHEN jc_type = 'UACR' AND jc_cnt >= 700 AND jc_cnt < 2000 THEN '700-1999'
        WHEN jc_type = 'UACR' AND jc_cnt >= 2000 AND jc_cnt < 5000 THEN '2000-4999'
        WHEN jc_type = 'UACR' AND jc_cnt >= 5000 THEN '>=5000'
        WHEN jc_type = 'UPCR' AND jc_cnt > 0 AND jc_cnt < 150 THEN '0-29'
        WHEN jc_type = 'UPCR' AND jc_cnt >= 150 AND jc_cnt < 500 THEN '30-199'
        WHEN jc_type = 'UPCR' AND jc_cnt >= 500 AND jc_cnt < 650 THEN '200-299'
        WHEN jc_type = 'UPCR' AND jc_cnt >= 500 AND jc_cnt < 1000 THEN '300-499'
        WHEN jc_type = 'UPCR' AND jc_cnt >= 1000 AND jc_cnt < 1500 THEN '500-699'
        WHEN jc_type = 'UPCR' AND jc_cnt >= 1500 AND jc_cnt < 3500 THEN '700-1999'
        WHEN jc_type = 'UPCR' AND jc_cnt >= 3500 AND jc_cnt < 8000 THEN '2000-4999'
        WHEN jc_type = 'UPCR' AND jc_cnt >= 8000 THEN '>=5000'
        WHEN jc_type = '24H' AND jc_cnt > 0 AND jc_cnt < 150 THEN '0-29'
        WHEN jc_type = '24H' AND jc_cnt >= 150 AND jc_cnt < 500 THEN '30-199'
        WHEN jc_type = '24H' AND jc_cnt >= 500 AND jc_cnt < 650 THEN '200-299'
        WHEN jc_type = '24H' AND jc_cnt >= 500 AND jc_cnt < 1000 THEN '300-499'
        WHEN jc_type = '24H' AND jc_cnt >= 1000 AND jc_cnt < 1500 THEN '500-699'
        WHEN jc_type = '24H' AND jc_cnt >= 1500 AND jc_cnt < 3500 THEN '700-1999'
        WHEN jc_type = '24H' AND jc_cnt >= 3500 AND jc_cnt < 8000 THEN '2000-4999'
        WHEN jc_type = '24H' AND jc_cnt >= 8000 THEN '>=5000'
        WHEN jc_cnt = '0' OR jc_cnt IS NULL THEN '缺失'
    END AS AgeRange
FROM jc_t_td2 AS a
JOIN CM AS b ON a.subjid = b.subjid
WHERE a.jc_dt < DATE_SUB(CURDATE(), INTERVAL 4 WEEK) 
    AND a.cohort = 'B'
    AND (b.CMTRT LIKE '%普利%'
        OR b.CMTRT LIKE '%利酮%'
        OR b.CMTRT LIKE '%沙坦%' 
        OR b.CMTRT LIKE '%列净%'
        OR b.CMTRT LIKE '%螺内酯%') 
    AND b.CMONGO = '1'
GROUP BY a.cohort, a.jc_type, AgeRange;
    
    
    
    
    
    
    select * from(select l.*,row_number() over (partition by l.SUBJID order by l.PAGEFSDT desc) x from LBCKD l
WHERE l.LBTEST3 = 2) a where x = 1

    
       SELECT  COUNT(DISTINCT c.subjid) AS count,
	 CASE
        WHEN A.LBORRES = '' or A.LBORRES IS NULL THEN '缺失'
        WHEN A.LBORRES >= 90 THEN '大于90'
        WHEN A.LBORRES >= 60 AND A.LBORRES < 90 THEN '60-90'
        WHEN A.LBORRES >= 45 AND A.LBORRES < 60 THEN '45-59'
        WHEN A.LBORRES >= 30 AND A.LBORRES < 45 THEN '30-44'
        WHEN A.LBORRES >= 15 AND A.LBORRES < 30 THEN '15-29'
        WHEN A.LBORRES < 15 THEN '小于15'
    END AS type    
 FROM (select * from(select l.*,row_number() over (partition by l.SUBJID order by l.PAGEFSDT desc) x from LBCKD l
WHERE l.LBTEST3 = 2) a where x = 1) as A, IE2 as c ,CM AS b 
 where A.SUBJID= c.subjid and A.SUBJID=b.subjid
    AND (b.CMTRT LIKE '%普利%'
        OR b.CMTRT LIKE '%利酮%'
        OR b.CMTRT LIKE '%螺内酯%') 
    AND b.CMONGO = '1'
 group by  A.LBORRES
 
 
 
 
 
 
 
select * from LBCKD LBTEST3_TXT like '%eGFR%' and LBORRES > 20 and LBORRES < 90



