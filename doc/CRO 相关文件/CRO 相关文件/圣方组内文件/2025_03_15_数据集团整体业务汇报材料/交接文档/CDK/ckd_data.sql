-- Database export via SQLPro (https://www.sqlprostudio.com/)
-- Exported by yuhengcai at 04-03-2025 16:26.
-- WARNING: This file may contain descructive statements such as DROPs.
-- Please ensure that you are running the script at the proper location.


DELIMITER $$
DROP PROCEDURE IF EXISTS process_DST $$
CREATE PROCEDURE `process_DST`(IN subjid_val VARCHAR(255))
BEGIN
    
	DECLARE dstyn1_val VARCHAR(255);
	DECLARE HOREAS_TXT_val VARCHAR(255);
    DECLARE HOREASOTH_val VARCHAR(255);
    DECLARE O19_val  VARCHAR(255);

    
    -- 查询LBURI1表中的数据并赋值给变量
      
     SELECT DST.dstyn1 into dstyn1_val FROM DST WHERE DST.SUBJID=subjid_val  ;
    -- SELECT DST.dstyn1 FROM DST WHERE DST.SUBJID='E130220012' dsty;
     -- E130220012
	               
    -- 根据条件判断O19_val的值
    if dstyn1_val is not null and dstyn1_val <> ''  then
         if dstyn1_val = 2 then    
       		set O19_val = '否';
       	 else 
       	 	set O19_val ='是';
       	 end if;	
     else
       set O19_val = '否';
    end if;
    
     -- 更新fuhedu表中的数据
    UPDATE fuhedu SET O19 = O19_val WHERE ID = subjid_val;

END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_DSTB $$
CREATE PROCEDURE `process_DSTB`(IN subjid_val VARCHAR(255))
BEGIN
    
	DECLARE dstyn1_val VARCHAR(255);
	DECLARE HOREAS_TXT_val VARCHAR(255);
    DECLARE HOREASOTH_val VARCHAR(255);
    DECLARE T20_val  VARCHAR(255);

    
    -- 查询LBURI1表中的数据并赋值给变量
      
     SELECT DST.dstyn1 into dstyn1_val FROM DST WHERE DST.SUBJID=subjid_val  ;
    -- SELECT DST.dstyn1 FROM DST WHERE DST.SUBJID='E130220012' dsty;
     -- E130220012
	               
    -- 根据条件判断O19_val的值
    if dstyn1_val is not null and dstyn1_val <> ''  then
         if dstyn1_val = 2 then    
       		set T20_val = '否';
       	 else 
       	 	set T20_val ='是';
       	 end if;	
     else
       set T20_val = '否';
    end if;
    
     -- 更新fuhedu表中的数据
    UPDATE fuheduB      SET T20 = T20_val WHERE ID = subjid_val;

END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_LBCHEM $$
CREATE PROCEDURE `process_LBCHEM`(IN subjid_val VARCHAR(255))
BEGIN
    DECLARE LBORRES_val VARCHAR(255);
    DECLARE LBORRES1_val VARCHAR(255);
    DECLARE LBTEST2_TXT_val VARCHAR(255);
    DECLARE LBORNRHI1_val VARCHAR(255);
    DECLARE LBORNRHI2_val VARCHAR(255);
    DECLARE J14_val VARCHAR(255);
    DECLARE K15_val VARCHAR(255);
    DECLARE L16_val VARCHAR(255);
    

    -- 查询LBURI1表中的数据并赋值给变量
    
   -- SELECT LBCHEM.SUBJID, LBCHEM.LBTEST2, LBCHEM.LBORRES, LBCHEM.LBTEST2_TXT FROM LBCHEM WHERE LBCHEM.LBTEST2 = 3 ;   
   select LBORRES into LBORRES_val from(select l.*,rank() over (partition by l.SUBJID order by l.PAGELMDT) x from LBCHEM l) as a where x = 1 and SUBJID=subjid_val and LBTEST2=3; 
   select LBORRES into LBORRES1_val from(select l.*,rank() over (partition by l.SUBJID order by l.PAGELMDT) x from LBCHEM l) as a where x = 1 and SUBJID=subjid_val and LBTEST2=4; 
   select LBORNRHI1 into LBORNRHI1_val from(select l.*,rank() over (partition by l.SUBJID order by l.PAGELMDT) x from LBCHEM l) as a where x = 1 and SUBJID=subjid_val and LBTEST2=3; 
   select LBORNRHI1 into LBORNRHI2_val from(select l.*,rank() over (partition by l.SUBJID order by l.PAGELMDT) x from LBCHEM l) as a where x = 1 and SUBJID=subjid_val and LBTEST2=4; 
  -- select LBORNRHI1  from(select l.*,rank() over (partition by l.SUBJID order by l.PAGELMDT) x from LBCHEM l) as a where x = 1  and LBTEST2=4; 
   select LBTEST2_TXT into LBTEST2_TXT_val from(select l.*,rank() over (partition by l.SUBJID order by l.PAGELMDT) x from LBCHEM l) as a where x = 1 and LBTEST2_TXT IN ('HIV-1', 'HIV-2', '乙型肝炎表面抗原阳性', '丙型肝炎病毒核酸检测阳性');
  -- select LBTEST2_TXT from(select l.*,rank() over (partition by l.SUBJID order by l.PAGELMDT) x from LBCHEM l) as a where x = 1 and  LBTEST2_TXT IN ('HIV-1', 'HIV-2', '乙型肝炎表面抗原阳性', '丙型肝炎病毒核酸检测阳性');
   -- select LBORRES  from(select l.*,rank() over (partition by l.SUBJID order by l.PAGELMDT) x from LBCHEM l) as a where x = 1 and LBTEST2=3; 
  -- select count(*) from LBCHEM where  LBTEST2=3  group by SUBJID  LBTEST2 like '%HIV-2%'
  -- select * from PR1 
   -- select *  from(select l.*,rank() over (partition by l.SUBJID order by l.PAGELMDT) x from LBCHEM l) as a where x = 1 and SUBJID='E130110006' and LBTEST2=3; 
   -- select *  from(select l.*,rank() over (partition by l.SUBJID order by l.PAGELMDT) x from LBCHEM l) as a where x = 1 and SUBJID='E130110006' and LBTEST2=4; 
  -- select *  from(select l.*,rank() over (partition by l.SUBJID order by l.PAGELMDT) x from LBCHEM l) as a where x = 1 and LBTEST2=5; 
  -- desc LBCHEMf
  
     IF LBORRES_val is not null or LBORRES1_val is not null then
         if LBORRES_val <>'' or LBORRES1_val<>'' or LBORNRHI1_val<>'' or LBORNRHI2_val<>''  then  
             /* set LBORRES_val=replace(LBORRES_val,'<','') ;
              set LBORNRHI1_val=replace(LBORNRHI1_val,'<','')*3;
              set LBORRES1_val=replace(LBORRES1_val,'<','');
              set LBORNRHI2_val=replace(LBORNRHI2_val,'<','')*3;*/
            if LBORRES_val<= 0 or LBORNRHI1_val <= 0 or LBORRES1_val <= 0 or LBORNRHI2_val <= 0 then
             set J14_val ='数据缺失';
            else
	         if LBORRES_val > LBORNRHI1_val*3 or LBORRES1_val > LBORNRHI2_val*3 then
	            SET  J14_val = '是';
	        ELSE
	            SET  J14_val = '否';
	        END IF;
	        
	      --  else
	        -- if LBORRES_val<=0 or  LBORNRHI1_val<=0 or LBORRES1_val<=0 or LBORNRHI2_val<=0
	        --  set J14_val ='数据缺失';

	        end if;
	       	       
	      else 
	         set J14_val ='数据缺失';
	      end if;
      else 
        set J14_val='数据缺失';
     end if;
     
     IF LBTEST2_TXT_val is not null THEN
          SET K15_val = '是';
        ELSE
          SET K15_val = '否';
     END IF;
     
    -- select subjid_val,LBORRES_val ,LBORRES1_val,LBORNRHI1_val,LBORNRHI1_val/3,LBORNRHI2_val,LBORNRHI2_val/3,J14_val;
    

    -- 根据条件判断B6的值
     -- 更新fuhedu表中的数据
    UPDATE fuhedu SET J14 = J14_val,K15 = K15_val,grouptext=1 WHERE ID = subjid_val;

END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_MH1B $$
CREATE PROCEDURE `process_MH1B`(IN subjid_val VARCHAR(255))
BEGIN
    DECLARE MH1TERM4_TXT_val INT;
    DECLARE K11_val VARCHAR(255);
    
    -- 查询MH1表中的数据并赋值给变量
    SELECT COUNT(*) INTO MH1TERM4_TXT_val FROM MH1 WHERE SUBJID = subjid_val AND MH1TERM4_TXT LIKE '%QT%';
    
    -- 根据条件判断K11的值
    IF MH1TERM4_TXT_val >= 1 THEN
        SET K11_val = '是';
    ELSE
        SET K11_val = '否';
    END IF;

    -- 更新fuheduB表中的数据
    UPDATE fuheduB SET K11 = K11_val WHERE ID = subjid_val;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_NYHA $$
CREATE PROCEDURE `process_NYHA`(IN subjid_val VARCHAR(255))
BEGIN
    DECLARE MHTERM_val VARCHAR(255);
    DECLARE MHTERM1_val VARCHAR(255);
    DECLARE MHTERM2_val VARCHAR(255);
    DECLARE MHTERM3_val VARCHAR(255);
    DECLARE D8_val VARCHAR(255);
    DECLARE F10_val VARCHAR(255);
    DECLARE I13_val VARCHAR(255);
    DECLARE P20_val VARCHAR(255);

    -- 查询LBURI1表中的数据并赋值给变量
     SELECT  MH.MHTERM into MHTERM_val FROM MH where MH.SUBJID=subjid_val AND MHSTDAT not like ('uk') and MHSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() and MHTERM IN ('NYHA III', 'V级心衰') ;
    -- SELECT  *  FROM MH where MH.SUBJID=subjid_val;
    SELECT MHTERM into MHTERM1_val  FROM MH WHERE  MH.MHTERM like '%1型糖尿病%' and MH.subjid = subjid_val LIMIT 1;
    -- SELECT MHTERM   FROM MH WHERE  MH.MHTERM = '1型糖尿病' and MH.subjid = 'E130050003';
    
    SELECT MHTERM into MHTERM2_val FROM MH WHERE  (MH.MHTERM LIKE'%癌%' OR MH.MHTERM LIKE '%肿瘤%') AND MH.subjid = subjid_val;
    SELECT MHTERM into MHTERM3_val FROM MH WHERE MH.MHTERM = '怀孕' and MH.subjid = subjid_val; 
   -- SELECT * FROM MH WHERE MH.MHTERM = '怀孕' and MH.subjid = subjid_val;
   -- SELECT * FROM MH WHERE  (MH.MHTERM LIKE'%癌%' OR MH.MHTERM LIKE '%肿瘤%') AND MH.subjid = subjid_val 
   -- SELECT * FROM MH WHERE   MH.MHTERM = '1型糖尿病' and MH.subjid = subjid_val
   /*
     SELECT  MH.MHTERM FROM MH where MH.SUBJID='E130051004' AND MHSTDAT not like ('uk') and MHSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 1 MONTH) AND NOW() and MHTERM IN ('NYHA III', 'V级心衰') ;
     SELECT MHTERM  FROM MH WHERE  MH.MHTERM like '%1型糖尿病%' and MH.subjid ='E130051004' LIMIT 1;
     SELECT MHTERM  FROM MH WHERE  (MH.MHTERM LIKE'%癌%' OR MH.MHTERM LIKE '%肿瘤%') AND MH.subjid = 'E130051004';
     SELECT MHTERM  FROM MH WHERE MH.MHTERM = '怀孕' and MH.subjid = 'E130051004'; */

    
     IF MHTERM_val is not null THEN
            SET D8_val = '是';
        ELSE
            SET D8_val = '否';
        END IF;
     IF MHTERM1_val is not null THEN
            SET F10_val = '是';
        ELSE
            SET F10_val = '否';
     END IF;
     
     IF MHTERM2_val is not null THEN
            SET I13_val = '是';
        ELSE
            SET I13_val = '否';
        END IF;
        
      IF MHTERM3_val is not null THEN
            SET P20_val = '是';
        ELSE
            SET P20_val = '否';
        END IF;


    -- 根据条件判断B6的值
     -- 更新fuhedu表中的数据
    UPDATE fuhedu SET D8 = D8_val,F10 = F10_val,I13 = I13_val,P20 = P20_val WHERE ID = subjid_val;

END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_NYHAB $$
CREATE PROCEDURE `process_NYHAB`(IN subjid_val VARCHAR(255))
BEGIN
    DECLARE MHTERM_val VARCHAR(255);
    DECLARE I9_val VARCHAR(255);
   
    -- 查询LBURI1表中的数据并赋值给变量
     SELECT  MH.MHTERM into MHTERM_val FROM MH where MH.SUBJID=subjid_val AND MHSTDAT not like ('uk') and MHSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() and MHTERM IN ('NYHA III', 'V级心衰') LIMIT 1;
       
     IF MHTERM_val is not null THEN
            SET I9_val = '是';
        ELSE
            SET I9_val = '否';
        END IF;
    

    -- 根据条件判断B6的值
     -- 更新fuhedu表中的数据
    UPDATE fuheduB SET I9 = I9_val WHERE ID = subjid_val;

END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_RASIB $$
CREATE PROCEDURE `process_RASIB`(IN subjid_val VARCHAR(255))
BEGIN
	DECLARE CMTRT_val VARCHAR(255);
    DECLARE D4_val VARCHAR(255);

/*
 SELECT *  FROM (
    SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
    FROM LBCKD l
    WHERE l.SUBJID = 'E130020005' AND l.LBTEST3 = 2 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
) AS a
WHERE x = 1;

*/
-- SELECT LBORRES INTO lborres_val FROM (SELECT l.*, (SELECT COUNT(*) FROM LBCKD WHERE SUBJID = l.SUBJID AND PAGEFSDT <= l.PAGEFSDT) AS rn FROM LBCKD l) AS sub WHERE rn = 1 AND SUBJID = subjid_val;

   -- SELECT  CM.CMTRT into CMTRT_val FROM CM where CM.SUBJID=subjid_val and CM.CMTRT in ('卡托普利', '依那普利', '贝那普利', '福辛普利', '雷米普利', '培哚普利', '咪达', '依普利酮或非奈利酮', '达格列净', '恩格列净', '卡格列净', '艾托格列净', '波生坦', '安立生坦', '马昔腾坦') LIMIT 1;
--   SELECT  * FROM CM where CM.SUBJID='E130071001' 
--   and CM.CMTRT in ('卡托普利', '依那普利', '贝那普利', '福辛普利', '雷米普利', '培哚普利', '咪达', '依普利酮或非奈利酮', '达格列净', '恩格列净', '卡格列净', '艾托格列净', '波生坦', '安立生坦', '马昔腾坦')

      /*SELECT  count(*) into CMTRT_val FROM CM where 
      CM.SUBJID=subjid_val 
   and (CM.CMTRT LIKE '%普利%' 
   OR CM.CMTRT LIKE '%沙坦%' 
  ) and CMONGO ='1' group by SUBJID;*/

  	  SELECT  count(*) into CMTRT_val FROM CM where 
      CM.SUBJID=subjid_val 
      and (CM.CMTRT LIKE '%普利%'
   OR CM.CMTRT LIKE '%利酮%'
   OR CM.CMTRT LIKE '%沙坦%' 
   OR CM.CMTRT LIKE '%列净%'
   OR CM.CMTRT LIKE '%螺内酯%'
   ) and CMONGO ='1'  group by SUBJID; -- AND CMSTDAT NOT LIKE '%uk%'  group by SUBJID;
  -- AND CMSTDAT < DATE_SUB(CURDATE(), INTERVAL 4 WEEK) group by SUBJID;

	/* SELECT  count(*)  FROM CM where 
     (CM.CMTRT LIKE '%普利%'
   OR CM.CMTRT LIKE '%利酮%'
   OR CM.CMTRT LIKE '%沙坦%' 
   OR CM.CMTRT LIKE '%列净%'
   OR CM.CMTRT LIKE '%螺内酯%'
   ) and CMONGO ='1'  AND CMSTDAT NOT LIKE '%uk%' 
   AND CMSTDAT < DATE_SUB(CURDATE(), INTERVAL 4 WEEK) group by SUBJID;      */  
        
	        IF CMTRT_val >= 1  THEN
	            SET D4_val = '是';
	        ELSE
	            SET D4_val = '否';
	        END IF;
	   
        -- SELECT CONCAT('UPDATE fuheduB SET A1 = ', A1_val, ' WHERE ID = ', subjid_val, ';');

     UPDATE fuheduB SET D4 = D4_val WHERE ID = subjid_val;
   End $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_SGB $$
CREATE PROCEDURE `process_SGB`(IN subjid_val VARCHAR(255))
BEGIN
	DECLARE MHTERM_val int;
	DECLARE MHTERM1_val int;
	DECLARE PRTRT_val int;
	DECLARE MHTERM2_val int;
    DECLARE L12_val VARCHAR(255);
	DECLARE M13_val VARCHAR(255);
	DECLARE N14_val VARCHAR(255);
	DECLARE O15_val VARCHAR(255);

	 SELECT count(*) into MHTERM_val  FROM MH WHERE  MH.MHTERM like '%Child-Pugh C%' and MH.subjid = subjid_val group by SUBJID ;
	 SELECT count(*) into MHTERM1_val from MH where  (MH.MHTERM like '%肾上腺皮质功能不全%' or MH.MHTERM like '%肾上腺功能不全%') and MH.subjid = subjid_val group by SUBJID ;
	 SELECT count(*) into PRTRT_val from PR where  PR.PRTRT like '%透析%' and subjid = subjid_val and PRSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() group by SUBJID;
	 SELECT count(*) into MHTERM2_val from MH where  MH.MHTERM like '%急性肾损伤%' and subjid = subjid_val and MHSTDAT not like ('%uk%') and MHSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() group by SUBJID;

	 -- select count(*)  from PR where  PR.PRTRT like '%透析%' and PRSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 3 MONTH) AND NOW() group by SUBJID;
		if MHTERM_val >= 1 then
		  	set L12_val = '是';
		else 
			set L12_val= '否';
		end if;
		
		if MHTERM1_val >= 1 then
		   set M13_val = '是';
		else 
			set M13_val = '否';
		end if;
		
		if PRTRT_val >= 1 then
		    set N14_val = '是';
		else
		    set N14_val = '否';
		end if;
		
		
		if MHTERM2_val >= 1 then
		    set O15_val = '是';
		else
		    set O15_val = '否';
		end if;
		
  	 					           
        -- SELECT CONCAT('UPDATE fuheduB SET A1 = ', A1_val, ' WHERE ID = ', subjid_val, ';');

     UPDATE fuheduB SET L12 = L12_val,M13 = M13_val,N14 = N14_val,O15 = O15_val,U21 = '否' WHERE ID = subjid_val;

   End $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_UACR $$
CREATE PROCEDURE `process_UACR`(IN subjid_val VARCHAR(255))
BEGIN
    DECLARE lborres_val VARCHAR(255);
    DECLARE lborres2_val VARCHAR(255);
    DECLARE lborres3_val VARCHAR(255);
    DECLARE lborres4_val VARCHAR(255);
    DECLARE lborres5_val VARCHAR(255);
    DECLARE lborres6_val VARCHAR(255);
     DECLARE lborres7_val VARCHAR(255);
    DECLARE lborres8_val VARCHAR(255);

    DECLARE B6_val VARCHAR(255);

    -- 查询LBURI1表中的数据并赋值给变量
    -- SELECT LBURI1.LBORRES6 INTO lborres_val FROM LBURI1  WHERE LBURI1.SUBJID = subjid_val AND LBURI1.lbtest8 = 4 and LBND=1;
    -- SELECT count(*), SUBJID FROM LBURI1  WHERE lbtest8 = 4 group by SUBJID;
    -- select * FROM LBURI1  WHERE lbtest8 = 5 and SUBJID='E130050006'and LBND=1; 4UACR   5UPCR
   -- SELECT LBURI1.LBORRES6 INTO lborres2_val FROM LBURI1  WHERE LBURI1.SUBJID = subjid_val AND LBURI1.lbtest8 = 5 and LBND=1;
    
--	select LBORRES into lborres3_val from LB24UP where Lbtest9=1 and subjid = subjid_val LIMIT 1;
--	select LBORRESU1_TXT into lborres4_val from LB24UP where Lbtest9=1 and subjid = subjid_val LIMIT 1;
--	select LBORRESUO into lborres5_val from LB24UP where Lbtest9=1 and subjid = subjid_val LIMIT 1;
	-- select LBORRES  from LB24UP where Lbtest9=1 and subjid = 'E130020004' LIMIT 1;
   -- select LBORRESU1_TXT from LB24UP where Lbtest9=1 and subjid = 'E130020004' LIMIT 1;
	-- select count(*) from LB24UP where Lbtest9=1 group by subjid
   -- SELECT LBORRES INTO lborres3_val FROM LBURI1  WHERE LBURI1.SUBJID = subjid_val AND LBURI1.lbtest8 = 5 and LBND=1;

	-- select LBORRESU1_TXT  from LB24UP where Lbtest9=1
    
    /* SELECT LBORRES6 INTO lborres_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LBURI1 l
        WHERE l.SUBJID = subjid_val AND l.LBTEST8 = 4 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;

    SELECT LBORRES6 INTO lborres2_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LBURI1 l
        WHERE l.SUBJID = subjid_val AND l.LBTEST8 = 5 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;
    

    
     
     SELECT LBORRESUO INTO lborres8_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LBURI1 l
        WHERE l.SUBJID = subjid_val AND l.LBTEST8 = 4 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;
    
    
      SELECT LBORRESUO INTO lborres7_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LBURI1 l
        WHERE l.SUBJID = subjid_val AND l.LBTEST8 = 5 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;

    
   
     SELECT LBORRES INTO lborres3_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LB24UP l
        WHERE l.SUBJID = subjid_val AND l.Lbtest9 = 1 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;

    SELECT LBORRESU1_TXT INTO lborres4_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LB24UP l
        WHERE l.SUBJID = subjid_val AND l.Lbtest9 = 1 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;

    SELECT LBORRESUO INTO lborres5_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LB24UP l
        WHERE l.SUBJID = subjid_val AND l.Lbtest9 = 1 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;*/
    
    SELECT jc_cnt INTO lborres_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.jc_dt) AS x
        FROM jc_t l
        WHERE l.SUBJID = subjid_val AND l.jc_type = 'UACR' AND l.jc_dt >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
    ) AS a
    WHERE x = 1 limit 1;
    
      SELECT jc_cnt INTO lborres2_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.jc_dt) AS x
        FROM jc_t l
        WHERE l.SUBJID = subjid_val AND l.jc_type = 'UPCR' AND l.jc_dt >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
    ) AS a
    WHERE x = 1  limit 1;
    
    SELECT jc_cnt INTO lborres6_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.jc_dt) AS x
        FROM jc_t l
        WHERE l.SUBJID = subjid_val AND l.jc_type = '24H' AND l.jc_dt >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
    ) AS a
    WHERE x = 1  limit 1;




    
    -- 根据条件判断B6的值
    
	 
	
    
      IF (lborres_val IS NOT NULL OR lborres_val <> '') OR (lborres2_val IS NOT NULL OR lborres2_val <> '') OR (lborres6_val IS NOT NULL OR lborres6_val <> '') THEN
        IF lborres_val > 700 OR lborres2_val > 1000 or lborres6_val >= 1000 THEN
            SET B6_val = '是';
        ELSEIF (lborres_val >= 500 AND lborres_val < 700) OR (lborres2_val > 800 AND lborres2_val <= 1000) or(lborres6_val>=800 and lborres6_val<=1000) THEN
            SET B6_val = '近似';
        ELSEIF lborres_val < 500 or lborres2_val < 800 or lborres6_val < 800 THEN
            SET B6_val = '否';
        END IF;
    ELSE
        SET B6_val = '数据缺失';
    END IF;

    -- 更新fuhedu表中的数据
    UPDATE fuhedu SET B6 = B6_val WHERE ID = subjid_val;

END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_UACRB $$
CREATE PROCEDURE `process_UACRB`(IN subjid_val VARCHAR(255))
BEGIN
    DECLARE lborres_val VARCHAR(255);
    DECLARE lborres2_val VARCHAR(255);
    DECLARE lborres3_val VARCHAR(255);
    DECLARE lborres4_val VARCHAR(255);
    DECLARE lborres5_val VARCHAR(255);
    DECLARE lborres6_val VARCHAR(255);
    DECLARE lborres7_val VARCHAR(255);
    DECLARE lborres8_val VARCHAR(255);
    DECLARE B2_val VARCHAR(255);

  /*  SELECT LBORRES6 INTO lborres_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LBURI1 l
        WHERE l.SUBJID = subjid_val AND l.LBTEST8 = 4 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;

    SELECT LBORRES6 INTO lborres2_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LBURI1 l
        WHERE l.SUBJID = subjid_val AND l.LBTEST8 = 5 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;
    
    
    -- 单位
    
     SELECT LBORRESUO INTO lborres8_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LBURI1 l
        WHERE l.SUBJID = subjid_val AND l.LBTEST8 = 4 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;
    
    
      SELECT LBORRESUO INTO lborres7_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LBURI1 l
        WHERE l.SUBJID = subjid_val AND l.LBTEST8 = 5 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;

--  

    SELECT LBORRES INTO lborres3_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LB24UP l
        WHERE l.SUBJID = subjid_val AND l.Lbtest9 = 1 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;

    SELECT LBORRESU1_TXT INTO lborres4_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LB24UP l
        WHERE l.SUBJID = subjid_val AND l.Lbtest9 = 1 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;

    SELECT LBORRESUO INTO lborres5_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LB24UP l
        WHERE l.SUBJID = subjid_val AND l.Lbtest9 = 1 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;

    IF lborres4_val IS NOT NULL THEN
        IF lborres4_val = 'g/24h' THEN
            SET lborres6_val = lborres3_val;
        ELSE
            IF lborres4_val = 'mg/24h' OR lborres4_val = '其它' THEN
                SET lborres6_val = lborres3_val / 1000;
            ELSE
                SET lborres6_val = 0;
            END IF;
        END IF;
    END IF;
    
    
    IF lborres7_val IS NOT NULL OR lborres7_val <>'' THEN
       IF lborres7_val like 'g/%' then
          set lborres2_val = lborres2_val*1000;
       else 
             set lborres2_val = lborres2_val;
       end if;
    end if;
       
       IF lborres8_val IS NOT NULL OR lborres8_val <> '' THEN
	       IF lborres8_val like 'g/%' then
	          set lborres_val = lborres_val*1000;
	       else 
	             set lborres_val = lborres_val;
       		end if;
		end if;*/
		
		SELECT jc_cnt INTO lborres_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.jc_dt) AS x
        FROM jc_t l
        WHERE l.SUBJID = subjid_val AND l.jc_type = 'UACR' AND l.jc_dt >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;
    
      SELECT jc_cnt INTO lborres2_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.jc_dt) AS x
        FROM jc_t l
        WHERE l.SUBJID = subjid_val AND l.jc_type = 'UPCR' AND l.jc_dt >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;
    
    SELECT jc_cnt INTO lborres6_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.jc_dt) AS x
        FROM jc_t l
        WHERE l.SUBJID = subjid_val AND l.jc_type = '24H' AND l.jc_dt >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
    ) AS a
    WHERE x = 1;
   

  

       

    IF (lborres_val IS NOT NULL OR lborres_val <> '') OR (lborres2_val IS NOT NULL OR lborres2_val <> '') OR (lborres6_val IS NOT NULL OR lborres6_val <> '') THEN
        IF (lborres_val > 500 AND lborres_val < 5000) OR (lborres2_val > 760 AND lborres2_val < 8000) OR (lborres6_val > 760 AND lborres6_val < 8000) THEN
            SET B2_val = '是';
        ELSEIF (lborres_val >= 100 AND lborres_val <= 150) OR (lborres_val >= 5000 AND lborres_val <= 6000) THEN
            SET B2_val = '近似';
        ELSEIF lborres_val < 100 OR lborres_val > 6000 THEN
            SET B2_val = '否';
        END IF;
    ELSE
        SET B2_val = '数据缺失';
    END IF;
   -- select B2_val;

    UPDATE fuheduB SET B2 = B2_val WHERE ID = subjid_val;
    
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_XS $$
CREATE PROCEDURE `process_XS`(IN subjid_val VARCHAR(255))
BEGIN
    
	DECLARE HOMETHOD_TXT_val VARCHAR(255);
	DECLARE HOREAS_TXT_val VARCHAR(255);
    DECLARE HOREASOTH_val VARCHAR(255);
    DECLARE HOREAS1_val VARCHAR(255);

    DECLARE E9_val VARCHAR(255);

    -- 查询LBURI1表中的数据并赋值给变量
     SELECT HO.HOMETHOD_TXT into HOMETHOD_TXT_val FROM HO where HO.SUBJID = subjid_val and HOSTDAT not like ('%uk%') and HOSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 WEEK) AND NOW() and HOREAS_TXT like('%心衰%') ;

     select HO.HOREAS_TXT into HOREAS_TXT_val FROM HO where HO.SUBJID = subjid_val and HOSTDAT not like ('%uk%') and HOSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 WEEK) AND NOW() and HOREAS_TXT like('%心衰%') ;

     select HO.HOREASOTH into HOREASOTH_val FROM HO where HO.SUBJID = subjid_val and HOSTDAT not like ('%uk%') and HOSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 WEEK) AND NOW() and HOREAS_TXT like('%心衰%') ;

     select HO.HOREAS1 into HOREAS1_val FROM HO where HO.SUBJID = subjid_val and HOSTDAT not like ('%uk%') and HOSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 WEEK) AND NOW() and HOREAS_TXT like('%心衰%') ;

    -- select HO.HOSTDAT into HOSTDAT_val FROM HO where HO.SUBJID = subjid_val and HOSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 4 WEEK) AND NOW();
  
    --  SELECT * FROM HO where HOSTDAT not like ('%uk%') and HOSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 4 WEEK) AND NOW() and HOREAS_TXT like('%心衰%') ;
    
	        IF HOMETHOD_TXT_val = '住院' AND (HOREAS_TXT_val = '心衰' OR HOREASOTH_val = '心衰' OR HOREAS1_val = '心衰') THEN
	            SET E9_val = '是';
	        ELSE
	            SET E9_val = '否';
	        END IF;
       
    -- 根据条件判断B6的值
     -- 更新fuhedu表中的数据
    UPDATE fuhedu SET E9 = E9_val WHERE ID = subjid_val;

END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data $$
CREATE PROCEDURE `process_data`()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE lbckdone INT DEFAULT 0;
    DECLARE subjid_val VARCHAR(255);
    DECLARE lobrrs_val FLOAT;
    -- DECLARE lbtest8_val INT;
    DECLARE CMTRT_val VARCHAR(255);
    DECLARE cmongo_val INT;
    DECLARE CMSTDAT_val DATE;
    DECLARE MHTERM_val VARCHAR(255);
    DECLARE HOSTDAT_val DATE;
    DECLARE HOMETHOD_TXT_val VARCHAR(255);
    DECLARE HOREAS_TXT_val VARCHAR(255);
    DECLARE HOREASOTH_val VARCHAR(255);
    DECLARE HOREAS1_val VARCHAR(255);
    DECLARE PR1TRT_val VARCHAR(255);
    DECLARE PR1DAT_val DATE;
    DECLARE PR2DAT_val_str VARCHAR(255);
    DECLARE LBTEST2_TXT_val VARCHAR(255);
    DECLARE CMDSTXT_val INT;
    DECLARE dstyn1_val INT;
    DECLARE LBURI1_subjid_val INT;
    -- DECLARE lobrrs_val FLOAT;
    DECLARE LBTEST8_val INT;
    DECLARE B6_status VARCHAR(10);
    DECLARE LBURI1done INT DEFAULT 0;
    DECLARE CMdone INT DEFAULT 0;
    DECLARE cm_subjid_val VARCHAR(255);
    --   DECLARE CMTRT_val VARCHAR(255);
    -- DECLARE cmongo_val INT;
    -- DECLARE CMSTDAT_val DATE;
    DECLARE C7_status VARCHAR(10);
    DECLARE MHdone INT DEFAULT 0;
    DECLARE MH_subjid_val VARCHAR(255);
    -- DECLARE MHTERM_val VARCHAR(255);
    DECLARE MHSTDAT_val DATE;
    DECLARE D8_status VARCHAR(10);
    DECLARE HOdone INT DEFAULT 0;
    DECLARE HO_subjid_val VARCHAR(255);
    -- DECLARE HOMETHOD_TXT_val VARCHAR(255);
    -- DECLARE HOREAS_TXT_val VARCHAR(255);
    -- DECLARE HOREASOTH_val VARCHAR(255);
    --  DECLARE HOREAS1_val VARCHAR(255);
    -- DECLARE HOSTDAT_val DATE;
    DECLARE E9_status VARCHAR(10);
    DECLARE F10_status VARCHAR(10);
    DECLARE I13_status VARCHAR(10);
    DECLARE O19_status VARCHAR(10);
    DECLARE P20_status VARCHAR(10);
    DECLARE PR2done INT DEFAULT 0;
    DECLARE PR2_subjid_val VARCHAR(255);
    DECLARE PR2TRT_val VARCHAR(255);
    DECLARE PR2DAT_val DATE;
    DECLARE G11_status VARCHAR(10);
    DECLARE H12_status VARCHAR(10);
    DECLARE lbchemdone INT DEFAULT 0;
    DECLARE lbchem_subjid_val VARCHAR(255);
    DECLARE LBTEST2_val INT;
    DECLARE LBORRES_val FLOAT;
    -- DECLARE LBTEST2_TXT_val VARCHAR(255);
    DECLARE J14_status VARCHAR(10);
    DECLARE L16_status VARCHAR(10);
    DECLARE M17_status VARCHAR(10);
    DECLARE N18_status VARCHAR(10);
   -- DECLARE CMDSTXT_val INT;
    DECLARE DSTdone INT DEFAULT 0;
    DECLARE dst_SUBJID_val INT;
    DECLARE CMSTDAT_val_str VARCHAR(18);
    DECLARE MHSTDAT_val_str VARCHAR(18);
   -- DECLARE dstyn1_val INT;


    -- Cursor for selecting subjid from DM table
    DECLARE cur CURSOR FOR SELECT SUBJID FROM DM;
 	DECLARE LBCKDcur CURSOR FOR  SELECT LBCKD.LBORRES FROM LBCKD WHERE LBCKD.SUBJID = subjid_val AND LBCKD.lbtest3 = 2;
 	DECLARE LBURI1cur CURSOR FOR SELECT LBURI1.SUBJID,LBURI1.LBORRES6,LBURI1.LBTEST8 FROM LBURI1  WHERE LBURI1.SUBJID = subjid_val AND LBURI1.lbtest8 IN (4, 5);
 	DECLARE CMcur CURSOR FOR SELECT CM.SUBJID, CM.CMTRT, CM.cmongo, CM.CMSTDAT FROM CM where CM.SUBJID=subjid_val;
 	DECLARE MHcur CURSOR FOR  SELECT MH.SUBJID, MH.MHTERM FROM MH where MH.SUBJID=subjid_val;
 	DECLARE HOcur CURSOR FOR SELECT HO.SUBJID, HO.HOMETHOD_TXT, HO.HOREAS_TXT, HO.HOREASOTH, HO.HOREAS1, HO.HOSTDAT FROM HO where  HO.SUBJID = subjid_val;
 	DECLARE PR2cur CURSOR FOR SELECT PR2.SUBJID, PR2.PR2TRT, PR2.PR2DAT FROM PR2 where PR2.SUBJID=subjid_val;
 	DECLARE lbchemcur CURSOR FOR SELECT LBCHEM.SUBJID, LBCHEM.LBTEST2, LBCHEM.LBORRES, LBCHEM.LBTEST2_TXT FROM LBCHEM WHERE LBCHEM.SUBJID=subjid_val and LBCHEM.LBTEST2 IN (3, 4);
    DECLARE cm2cur CURSOR FOR  SELECT CM.SUBJID, CM.CMTRT, CM.cmongo, CM.CMDSTXT, CM.CMSTDAT FROM CM where CM.SUBJID = subjid_val;
    DECLARE DSTcur CURSOR FOR SELECT DST.SUBJID, DST.dstyn1 FROM DST WHERE DST.SUBJID=subjid_val;

      

    -- Error handling
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
	-- DECLARE CONTINUE HANDLER FOR NOT FOUND SET lbckdone = 1;
    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO subjid_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;

        -- Insert subjid into fuhedu table ID field
        INSERT INTO fuhedu (ID) VALUES (subjid_val);

        -- Process LBCKD data
        
               
        OPEN LBCKDcur;
        read_lbckd_loop: LOOP
            FETCH LBCKDcur INTO lobrrs_val;
            IF done THEN
                LEAVE read_lbckd_loop;
            END IF;

            IF lobrrs_val IS NOT NULL THEN
                IF lobrrs_val >= 20 AND lobrrs_val < 90 THEN
                    UPDATE fuhedu SET A5 = '是' WHERE ID = subjid_val;
                    else 
                    UPDATE fuhedu SET A5 = '否' WHERE ID = subjid_val;
                END IF;
             ELSE
                    UPDATE fuhedu SET A5 = '数据缺失' WHERE ID = subjid_val;
             END IF;
        END LOOP;
        CLOSE LBCKDcur;
        

        -- Process LBURI1 data
        -- Similar logic as LBCKD
            -- Error handling
   -- DECLARE CONTINUE HANDLER FOR NOT FOUND SET LBURI1done = 1;

    OPEN LBURI1cur;

    read_LBURI1_loop: LOOP
        FETCH LBURI1cur INTO LBURI1_subjid_val, lobrrs_val, LBTEST8_val;
        IF done THEN
            LEAVE read_LBURI1_loop;
        END IF;

        -- Determine B6 status based on conditions
        IF (lobrrs_val > 700 AND LBTEST8_val = 4) OR (lobrrs_val > 1000 AND LBTEST8_val = 5) THEN
            SET B6_status = '是';
        ELSE
            SET B6_status = '否';
        END IF;

        -- Update fuhedu table
        UPDATE fuhedu SET B6 = B6_status WHERE ID = LBURI1_subjid_val;
    END LOOP;
		 CLOSE LBURI1cur;
		 
		 
		 
        -- Process CM data
        -- Similar logic as LBCKD
    


    -- Error handling
    -- DECLARE CONTINUE HANDLER FOR NOT FOUND SET CMdone = 1;

    OPEN CMcur;

    read_CM_loop: LOOP
        FETCH CMcur INTO cm_subjid_val, CMTRT_val, cmongo_val, CMSTDAT_val_str;
        IF done THEN
            LEAVE read_CM_loop;
        END IF;

        -- Determine C7 status based on conditions
      
        if CMSTDAT_val_str not like CONCAT('%uk%') then 
            -- CMSTDAT_val = STR_TO_DATE (CMSTDAT_val_str, '%Y-%m-%d');
	        IF CMTRT_val IN ('卡托普利', '依那普利', '贝那普利', '福辛普利', '雷米普利', '培哚普利', '咪达', '依普利酮或非奈利酮', '达格列净', '恩格列净', '卡格列净', '艾托格列净', '波生坦', '安立生坦', '马昔腾坦') AND CMSTDAT_val_str BETWEEN DATE_SUB(NOW(), INTERVAL 4 WEEK) AND NOW() THEN
	            SET C7_status = '是';
	        ELSE
	            SET C7_status = '否';
	        END IF;
        end if;

        -- Update fuhedu table
        UPDATE fuhedu SET C7 = C7_status WHERE ID = cm_subjid_val;
    END LOOP;

    CLOSE CMcur;    

        -- Process MH data
        -- Similar logic as LBCKD
        

    -- Error handling
    -- DECLARE CONTINUE HANDLER FOR NOT FOUND SET MHdone = 1;

    OPEN MHcur;

    read_MH_loop: LOOP
        FETCH MHcur INTO MH_subjid_val, MHTERM_val;
        IF done THEN
            LEAVE read_MH_loop;
        END IF;

        -- Determine D8 status based on conditions
        IF MHTERM_val IN ('NYHA III', 'V级心衰') THEN
            SET D8_status = '是';
        ELSE
            SET D8_status = '否';
        END IF;

        -- Update fuhedu table
        UPDATE fuhedu SET D8 = D8_status WHERE ID = MH_subjid_val;
    END LOOP;

    CLOSE MHcur;
               
               
        -- Process HO data
        -- Similar logic as LBCKD
        
       
    -- Error handling
   -- DECLARE CONTINUE HANDLER FOR NOT FOUND SET HOdone = 1;

    OPEN HOcur;

    read_HO_loop: LOOP
        FETCH HOcur INTO HO_subjid_val, HOMETHOD_TXT_val, HOREAS_TXT_val, HOREASOTH_val, HOREAS1_val, HOSTDAT_val;
        IF done THEN
            LEAVE read_HO_loop;
        END IF;

        -- Determine E9 status based on conditions
        if HOSTDAT_val not like CONCAT('%uk%')  then
	        IF HOSTDAT_val >= DATE_SUB(NOW(), INTERVAL 6 MONTH) AND (HOMETHOD_TXT_val = '住院') AND (HOREAS_TXT_val = '心衰' OR HOREASOTH_val = '心衰' OR HOREAS1_val = '心衰') THEN
	            SET E9_status = '是';
	        ELSE
	            SET E9_status = '否';
	        END IF;
       end if;

        -- Determine F10 status based on conditions
        IF EXISTS (SELECT 1 FROM MH WHERE MH.subjid = HO_subjid_val AND MH.MHTERM like '%1型糖尿病%') THEN
            SET F10_status = '是';
        ELSE
            SET F10_status = '否';
        END IF;

        -- Determine I13 status based on conditions
        IF EXISTS (SELECT 1 FROM MH WHERE MH.subjid = HO_subjid_val AND (MH.MHTERM LIKE'%癌%' OR MH.MHTERM LIKE '%肿瘤%')) THEN
            SET I13_status = '是';
        ELSE
            SET I13_status = '否';
        END IF;
        
        
        IF EXISTS (SELECT 1 FROM MH WHERE MH.subjid = HO_subjid_val AND (MH.MHTERM = '怀孕')) THEN
            SET P20_status = '是';
        ELSE
            SET P20_status = '否';
        END IF;
        

        -- Update fuhedu table
        UPDATE fuhedu SET E9 = E9_status, F10 = F10_status, I13 = I13_status WHERE ID = HO_subjid_val;
    END LOOP;

    CLOSE HOcur;
                
        

        -- Process PR2 data
        -- Similar logic as LBCKD



    -- Error handling
   -- DECLARE CONTINUE HANDLER FOR NOT FOUND SET PR2done = 1;

    OPEN PR2cur;

    read_PR2_loop: LOOP
        FETCH PR2cur INTO PR2_subjid_val, PR2TRT_val, PR2DAT_val_str;
        IF done THEN
            LEAVE read_PR2_loop;
        END IF;

        -- Determine G11 and H12 status based on conditions
        if PR2DAT_val_str not like CONCAT('%uk%') or PR2DAT_val_str<>''then
        IF PR2DAT_val_str >= DATE_SUB(NOW(), INTERVAL 3 MONTH) AND 
           (PR1TRT_val IN ('有实体器官移植,骨髓移植史', '心肌梗死、心绞痛、脑血管事件、颈动脉手术、冠状动脉搭桥术、经皮冠状动脉介入术、经导管主动脉瓣植入术，瓣膜置换术')) THEN
            SET G11_status = '是';
            SET H12_status = '是';
        ELSE
            SET G11_status = '否';
            SET H12_status = '否';
        END IF;
        end if;

        -- Update fuhedu table
        UPDATE fuhedu SET G11 = G11_status, H12 = H12_status WHERE ID = PR2_subjid_val;
    END LOOP;

    CLOSE PR2cur;        




        -- Process lbchem data
        -- Similar logic as LBCKD
       

    -- Error handling
    -- DECLARE CONTINUE HANDLER FOR NOT FOUND SET lbchemdone = 1;

    OPEN lbchemcur;

    read_lbchem_loop: LOOP
        FETCH lbchemcur INTO lbchem_subjid_val, LBTEST2_val, LBORRES_val, LBTEST2_TXT_val;
        IF done THEN
            LEAVE read_lbchem_loop;
        END IF;

        -- Determine J14 and L16 status based on conditions
        IF (LBTEST2_val = 3 AND LBORRES_val > 3) OR (LBTEST2_val = 4 AND LBORRES_val > 3) THEN
            SET J14_status = '是';
        ELSE
            SET J14_status = '否';
        END IF;

        IF LBTEST2_TXT_val IN ('HIV-1', 'HIV-2', '乙型肝炎表面抗原阳性', '丙型肝炎病毒核酸检测阳性') THEN
            SET L16_status = '是';
        ELSE
            SET L16_status = '否';
        END IF;

        -- Update fuhedu table
        UPDATE fuhedu SET J14 = J14_status, K15 = '否', L16 = L16_status WHERE ID = lbchem_subjid_val;
    END LOOP;

    CLOSE lbchemcur;

        -- Process DST data
        -- Similar logic as LBCKD
        
       

    -- Error handling
   -- DECLARE CONTINUE HANDLER FOR NOT FOUND SET cm2done = 1;

    OPEN cm2cur;

    read_cm_loop: LOOP
        FETCH cm2cur INTO cm_subjid_val, CMTRT_val, cmongo_val, CMDSTXT_val, CMSTDAT_val_str;
        IF done THEN
            LEAVE read_cm_loop;
        END IF;

        -- Determine M17 and N18 status based on conditions
        if CMSTDAT_val not like CONCAT('%uk%') then
        IF CMSTDAT_val >= DATE_SUB(NOW(), INTERVAL 6 MONTH) AND cmongo_val = 1 AND 
           ((CMTRT_val = '泼尼松' AND CMDSTXT_val <= 10) OR 
            (CMTRT_val = '硫唑嘌呤' AND CMDSTXT_val <= 100) OR 
            (CMTRT_val = '吗替麦考酚酯' AND CMDSTXT_val <= 1000)) THEN
            SET M17_status = '是';
        ELSE
            SET M17_status = '否';
        END IF;
        end if;

        IF CMTRT_val IN ('英夫利昔单抗', '伊那西普', '托珠单抗') THEN
            SET N18_status = '是';
        ELSE
            SET N18_status = '否';
        END IF;

        -- Update fuhedu table
        UPDATE fuhedu SET M17 = M17_status, N18 = N18_status WHERE ID = cm_subjid_val;
    END LOOP;
	CLOSE cm2cur;
	
	-- DSTdata
        
       

    -- Error handling
    -- DECLARE CONTINUE HANDLER FOR NOT FOUND SET DSTdone = 1;

    OPEN DSTcur;

    read_dst_loop: LOOP
        FETCH DSTcur INTO dst_SUBJID_val, dstyn1_val;
        IF done THEN
            LEAVE read_dst_loop;
        END IF;

        -- Determine O19 status based on dstyn1 value
        IF dstyn1_val = 2 THEN
            UPDATE fuhedu SET O19 = '否' WHERE ID = dst_SUBJID_val;
        ELSE
            UPDATE fuhedu SET O19 = '是' WHERE ID = dst_SUBJID_val;
        END IF;
    END LOOP;

    CLOSE DSTcur;
    
            
        
    END LOOP;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_dataB $$
CREATE PROCEDURE `process_dataB`()
BEGIN
	DECLARE done INT DEFAULT FALSE;   
    DECLARE subjid_val VARCHAR(255);
	 DECLARE cur CURSOR FOR SELECT SUBJID FROM IE where IEYN <> '2';
	-- DECLARE cur CURSOR FOR SELECT SUBJID FROM IE where COHORT=2;
	DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
	
	OPEN cur;

	read_dm_loop: LOOP
	    FETCH cur INTO subjid_val;
	    IF done THEN
	        LEAVE read_dm_loop;
	    END IF;
	    
	 INSERT INTO fuheduB (ID,ICf_dt,date) VALUES (subjid_val,'',now());
	   
	    call process_eGFRB(subjid_val);
	    call process_UACRB(subjid_val);
	    call process_RASIB(subjid_val);
	   call process_xyB(subjid_val);
	    call process_xjB(subjid_val);
	    call process_tnbB(subjid_val);
	    call process_NYHAB(subjid_val);
	    call process_xnsjB(subjid_val);
       call process_MH1B(subjid_val);
	   call process_SGB(subjid_val);
	  call process_yongyaoB(subjid_val);
	    call process_DSTB(subjid_val);
	   
    END LOOP read_dm_loop;

CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board $$
CREATE PROCEDURE `process_data_board`()
BEGIN
    DECLARE done INT DEFAULT FALSE;   
    DECLARE siteid_val INT;
    DECLARE sitenm_val VARCHAR(255);
	DECLARE COHORT_val VARCHAR(255);
	DECLARE COHORT1_val VARCHAR(255);
	DECLARE site_count INT;
       
    DECLARE cur CURSOR FOR 
        SELECT siteid, count(SITEID),SITENM,COHORT 
        FROM IE where IEYN <> '2'
        GROUP BY siteid,sitenm,COHORT;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO siteid_val,site_count,sitenm_val,COHORT_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;
        
        -- 在这里添加您的逻辑
        if COHORT_val=1 then
        	set COHORT1_val ='A';
        else
        	set COHORT1_val ='B';
         end if;       
         INSERT INTO  board_t (allcount,sitename,siteid,cohort) value(site_count,sitenm_val,siteid_val,COHORT1_val);
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_24H $$
CREATE PROCEDURE `process_data_board_24H`()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE siteid_val INT;
    DECLARE siteid1_val INT;
    DECLARE sitenm_val VARCHAR(255);
    DECLARE COHORT_val VARCHAR(255);
    DECLARE COHORT1_val VARCHAR(255);
    DECLARE AgeRange_val VARCHAR(255);
    DECLARE site_count INT;
    DECLARE AgeRange1_val INT;
	    DECLARE cur CURSOR FOR 
	    /*SELECT COUNT(B.subjid) AS count,
    CASE
        WHEN A.LBORRES = '' OR A.LBORRES IS NULL THEN '缺失值'
        WHEN A.LBORRES <= 0.5 THEN '≤0.5'
        WHEN A.LBORRES > 0.5 AND A.LBORRES < 1 THEN '0.6-0.9'
        WHEN A.LBORRES >= 1 AND A.LBORRES <= 3.5 THEN '1-3.5'
        WHEN A.LBORRES > 3.5 THEN '>3.5'
    END AS AgeRange,
    CASE
        WHEN A.LBORRES = '' OR A.LBORRES IS NULL THEN 5
        WHEN A.LBORRES <= 0.5 THEN 1
        WHEN A.LBORRES > 0.5 AND A.LBORRES < 1 THEN 2
        WHEN A.LBORRES >= 1 AND A.LBORRES <= 3.5 THEN 3
        WHEN A.LBORRES >= 3.5 THEN 4
    END AS AgeRange1, A.SITEID,B.SITEID, A.SITENM, B.COHORT
FROM IE as B LEFT JOIN LB24UP as A ON A.SUBJID = B.SUBJID 
GROUP BY AgeRange,AgeRange1, A.SITEID,B.SITEID, A.SITENM, B.COHORT
order by AgeRange1 ;

SELECT COUNT(B.SUBJID) AS count,
 CASE
        WHEN A.LBORRES = '' OR A.LBORRES IS NULL THEN '缺失'
        WHEN A.LBORRES <= 0.5 THEN '≤0.5'
        WHEN A.LBORRES > 0.5 AND A.LBORRES < 1 THEN '0.6-0.9'
        WHEN A.LBORRES >= 1 AND A.LBORRES <= 3.5 THEN '1-3.5'
        WHEN A.LBORRES > 3.5 THEN '>3.5'
    END AS AgeRange,
    CASE
        WHEN A.LBORRES = '' OR A.LBORRES IS NULL THEN 5
        WHEN A.LBORRES <= 0.5 THEN 1
        WHEN A.LBORRES > 0.5 AND A.LBORRES < 1 THEN 2
        WHEN A.LBORRES >= 1 AND A.LBORRES <= 3.5 THEN 3
        WHEN A.LBORRES >= 3.5 THEN 4
    END AS AgeRange1 ,A.SITEID,B.SITEID, A.SITENM, B.COHORT
 FROM IE as B
LEFT JOIN (
select * from(select l.*,row_number() over (partition by l.SUBJID order by l.PAGEFSDT desc) x from LB24UP l
 where LBTEST9=1) a where x = 1
)A ON A.SUBJID = B.SUBJID where B.IEYN <> '2'
GROUP BY AgeRange,AgeRange1, A.SITEID,B.SITEID, A.SITENM, B.COHORT
ORDER BY AgeRange1;*/


select COUNT(B.SUBJID), 
CASE 
        WHEN A.jc_cnt > 0  and A.jc_cnt < 150 THEN '0-149'
        WHEN A.jc_cnt >= 150 AND A.jc_cnt < 500 THEN '150-499'
        WHEN A.jc_cnt >=500 AND A.jc_cnt < 649 THEN '500-649'
        WHEN A.jc_cnt >= 500 AND A.jc_cnt < 1000 THEN '500-999 '
	    WHEN A.jc_cnt >= 1000 AND A.jc_cnt < 1500 THEN '1000-1499'
	    WHEN A.jc_cnt >= 1500 AND A.jc_cnt < 3500 THEN '1500-3499'
		WHEN A.jc_cnt >= 3500 AND A.jc_cnt < 8000 THEN '3500-7999'
		WHEN A.jc_cnt >=8000 THEN '>=8000'
		WHEN A.jc_cnt  = '' OR A.jc_cnt IS NULL THEN '缺失'
	    END AS AgeRange,
    CASE 
        WHEN A.jc_cnt > 0  and A.jc_cnt < 150 THEN 0
        WHEN A.jc_cnt >= 150 AND A.jc_cnt < 500 THEN 1
        WHEN A.jc_cnt >=500 AND A.jc_cnt < 649 THEN 2
        WHEN A.jc_cnt >= 500 AND A.jc_cnt < 1000 THEN 3
	    WHEN A.jc_cnt >= 1000 AND A.jc_cnt < 1500 THEN 4
	    WHEN A.jc_cnt >= 1500 AND A.jc_cnt < 3500 THEN 5
		WHEN A.jc_cnt >= 3500 AND A.jc_cnt < 8000 THEN 6
		WHEN A.jc_cnt >=8000 THEN 7
		WHEN A.jc_cnt  = '' OR A.jc_cnt IS NULL THEN 8
		END AS AgeRange1, A.SITEID,B.SITEID, A.SITENM, B.COHORT
FROM IE as B
LEFT JOIN (
select * from(select l.*,row_number() over (partition by l.SUBJID ) x from jc_t l
WHERE l.jc_type = '24H') a where x = 1
) as A ON A.SUBJID = B.SUBJID where B.IEYN <> '2'
GROUP BY  AgeRange,AgeRange1,A.SITEID,B.SITEID, A.SITENM, B.COHORT
ORDER BY AgeRange1;




    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO site_count, AgeRange_val,AgeRange1_val, siteid_val, siteid1_val, sitenm_val, COHORT_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;

        -- 重置变量
		if COHORT_val=1 then
        	set COHORT1_val ='A';
        else
        	set COHORT1_val ='B';
         end if;  
         
         if siteid_val is null then
           set siteid_val = siteid1_val;
         end if;
         
          if AgeRange_val is null then
        	set AgeRange_val = '缺失';	
        	set AgeRange1_val = 8;
		end if;		
        -- 插入数据到 board_t 表中
        INSERT INTO board_t (
            sitename, 
            siteid, 
            cohort, 
            LBORRES_txt,
			LBORRES_count,
			LBORRES_row
			)
        VALUES (
            sitenm_val, 
            siteid_val, 
            COHORT1_val,
            AgeRange_val,
            site_count,
            AgeRange1_val
            );
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_24H_jc $$
CREATE PROCEDURE `process_data_board_24H_jc`()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE SUBJID_val VARCHAR(255);
    DECLARE siteid_val VARCHAR(255);
    DECLARE SITENM_val VARCHAR(255);
    DECLARE COHORT_val VARCHAR(255);
    DECLARE COHORT1_val VARCHAR(255);
    DECLARE LBORRES6_val VARCHAR(255);
    DECLARE LBUORRESU1_val VARCHAR(255);
    DECLARE LBUORRESU1_TXT_val VARCHAR(255);
    DECLARE PAGEFSDT_val VARCHAR(255);

    DECLARE cur CURSOR FOR
        SELECT B.SUBJID, B.SITEID, B.SITENM, B.COHORT, A.LBORRES, A.LBORRESU1, A.LBORRESU1_TXT,A.PAGEFSDT
        FROM IE as B
        LEFT JOIN (
            SELECT l.*, ROW_NUMBER() OVER (PARTITION BY l.SUBJID ORDER BY l.PAGEFSDT DESC) x
            FROM LB24UP l
            WHERE l.LBTEST9 = 1
        ) A ON A.SUBJID = B.SUBJID
        WHERE B.IEYN <> '2' AND A.x = 1 ;
        
        
        
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO SUBJID_val, siteid_val, SITENM_val, COHORT_val, LBORRES6_val, LBUORRESU1_val, LBUORRESU1_TXT_val,PAGEFSDT_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;

        -- 处理 LBORRES6_val 为空或 NULL 的情况
       
        -- 根据 cohort 设置 cohort1
        IF COHORT_val = '1' THEN
            SET COHORT1_val = 'A';
        ELSE
            SET COHORT1_val = 'B';
        END IF;

        -- 处理 LBUORRESU1_val 逻辑
        IF LBORRES6_val IS NOT NULL AND (LBORRES6_val < 15) THEN
            SET LBORRES6_val = LBORRES6_val * 1000;
        END IF;

        -- 插入数据到 jc_t 表中
        INSERT INTO jc_t (
            subjid,
            siteid,
            sitenm,
            cohort,
            jc_type,
            jc_name,
            jc_cnt,
            jc_dt
        )
        VALUES (
            SUBJID_val, siteid_val, SITENM_val, COHORT1_val, '24H', LBUORRESU1_val, LBORRES6_val,PAGEFSDT_val
        );
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_Pro $$
CREATE PROCEDURE `process_data_board_Pro`()
BEGIN
    DECLARE done INT DEFAULT FALSE;   
    DECLARE siteid_val INT;
    DECLARE siteid1_val INT;
    DECLARE sitenm_val VARCHAR(255);
    DECLARE COHORT_val VARCHAR(255);
    DECLARE COHORT1_val VARCHAR(255);
    DECLARE AgeRange_val VARCHAR(255);
    DECLARE site_count INT;
    DECLARE AgeRange1_val INT;
   

    DECLARE cur CURSOR FOR 
    /*SELECT
        COUNT(A.SUBJID) AS count,
        CASE
            WHEN A.LBORRES3_TXT = '' OR A.LBORRES3_TXT IS NULL THEN '尿蛋白为空'
            WHEN A.LBORRES3_TXT = '1-' AND A.LBORNRHI1='阴性' THEN '阴性／-'
            WHEN A.LBORRES3_TXT = '1+' THEN '+/阳性'
            WHEN A.LBORRES3_TXT = '2+' THEN '阳性++'
            WHEN A.LBORRES3_TXT >= '3+' THEN '+++及以上'
            WHEN A.LBORRES3_TXT >= '±' THEN '弱阳性'
        END AS AgeRange,
        CASE
            WHEN A.LBORRES3_TXT = '' OR A.LBORRES3_TXT IS NULL THEN 6
            WHEN A.LBORRES3_TXT = '1-' AND A.LBORNRHI1='阴性' THEN 1
            WHEN A.LBORRES3_TXT = '1+' THEN 2
            WHEN A.LBORRES3_TXT = '2+' THEN 3
            WHEN A.LBORRES3_TXT >= '3+' THEN 4
            WHEN A.LBORRES3_TXT >= '±' THEN 5
        END AS AgeRange1,
        A.SITEID,
        B.SITENM,
        B.COHORT
    FROM  IE as B LEFT JOIN LBURI as A ON A.SITEID = B.siteid AND A.subjid = B.subjid
    WHERE A.LBTEST7 = 1
    GROUP BY AgeRange, AgeRange1, A.SITEID, B.SITENM, B.COHORT
    ORDER BY AgeRange1;*/
    
SELECT COUNT(B.SUBJID) AS count,
         CASE
            WHEN A.LBORRES3_TXT = '' OR A.LBORRES3_TXT IS NULL THEN '缺失'
            WHEN A.LBORRES3_TXT = '1-' AND A.LBORNRHI1='阴性' THEN '-'
            WHEN A.LBORRES3_TXT = '1+' THEN '+'
            WHEN A.LBORRES3_TXT = '2+' THEN '++'
            WHEN A.LBORRES3_TXT >= '3+' THEN '+++及以上'
            WHEN A.LBORRES3_TXT >= '±' THEN '±'
        END AS AgeRange,
        CASE
            WHEN A.LBORRES3_TXT = '' OR A.LBORRES3_TXT IS NULL THEN 6
            WHEN A.LBORRES3_TXT = '1-' AND A.LBORNRHI1='阴性' THEN 1
            WHEN A.LBORRES3_TXT = '1+' THEN 2
            WHEN A.LBORRES3_TXT = '2+' THEN 3
            WHEN A.LBORRES3_TXT >= '3+' THEN 4
            WHEN A.LBORRES3_TXT >= '±' THEN 5
        END AS AgeRange1 ,A.SITEID,B.SITEID, A.SITENM, B.COHORT
 FROM IE as B
LEFT JOIN (
select * from(select l.*,row_number() over (partition by l.SUBJID order by l.PAGEFSDT desc) x from LBURI l
 where LBTEST7=1) a where x = 1
)A ON A.SUBJID = B.SUBJID where B.IEYN <> '2'
GROUP BY AgeRange,AgeRange1, A.SITEID,B.SITEID, A.SITENM, B.COHORT
ORDER BY AgeRange1;


    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO site_count, AgeRange_val, AgeRange1_val, siteid_val,siteid1_val, sitenm_val, COHORT_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;
        
        -- 重置变量
               
        IF COHORT_val=1 THEN
           SET COHORT1_val='A';
        ELSE
           SET COHORT1_val='B';
        END IF;
        
         if siteid_val is null then
           set siteid_val = siteid1_val;
         end if;
        
        -- 插入数据到 board_t 表中
        INSERT INTO board_t (sitename, siteid, cohort,LBORRES3_txt, LBORRES3_count)
        VALUES (sitenm_val, siteid_val, COHORT1_val,AgeRange_val,site_count);
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_SYSBP $$
CREATE PROCEDURE `process_data_board_SYSBP`()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE siteid_val INT;
    
    DECLARE sitenm_val VARCHAR(255);
    DECLARE COHORT_val VARCHAR(255);
    DECLARE COHORT1_val VARCHAR(255);
    DECLARE AgeRange_val VARCHAR(255);
    DECLARE site_count INT;
    DECLARE siteid1_val INT;
    DECLARE AgeRange1_val INT;
        
    DECLARE cur CURSOR FOR 
    /*SELECT COUNT(A.subjid) AS count,
    CASE
        WHEN A.SYSBP < 120  THEN '<120'
        WHEN A.SYSBP >= 120 AND A.SYSBP < 130 THEN '120-129'
        WHEN A.SYSBP >=130 AND A.SYSBP < 140 THEN '130-139'
        WHEN A.SYSBP >= 140 AND A.SYSBP < 150 THEN '140-149'
		WHEN A.SYSBP >= 150 AND A.SYSBP < 160 THEN '150-159'
		WHEN A.SYSBP >= 160 AND A.SYSBP < 170 THEN '160-169'
		WHEN A.SYSBP >= 170 AND A.SYSBP <= 180 THEN '170-179'
        WHEN A.SYSBP > 180 THEN '>180'
        WHEN A.SYSBP IS NULL THEN '缺失值'
    END AS AgeRange,
    CASE
        WHEN A.SYSBP < 120  THEN 0
        WHEN A.SYSBP >= 120 AND A.SYSBP < 130 THEN 1
        WHEN A.SYSBP >=130 AND A.SYSBP < 140 THEN 2
        WHEN A.SYSBP >= 140 AND A.SYSBP < 150 THEN 3
		WHEN A.SYSBP >= 150 AND A.SYSBP < 160 THEN 4
		WHEN A.SYSBP >= 160 AND A.SYSBP < 170 THEN 5
		WHEN A.SYSBP >= 170 AND A.SYSBP <= 180 THEN 6
        WHEN A.SYSBP > 180 THEN 7
        WHEN A.SYSBP IS NULL THEN 8
    END AS AgeRange1,A.SITEID,B.SITEID, A.SITENM, B.COHORT
FROM IE as B LEFT JOIN VS as A ON A.SUBJID = B.SUBJID
GROUP BY AgeRange,AgeRange1,A.SITEID,B.SITEID, A.SITENM, B.COHORT
ORDER BY AgeRange1;
*/

SELECT COUNT(B.subjid) AS count,
    CASE
        WHEN A.SYSBP <= 120  THEN '<=120'
        WHEN A.SYSBP > 120 AND A.SYSBP < 130 THEN '121-129'
        WHEN A.SYSBP >=130 AND A.SYSBP < 140 THEN '130-139'
        WHEN A.SYSBP >= 140 AND A.SYSBP < 150 THEN '140-149'
		WHEN A.SYSBP >= 150 AND A.SYSBP < 160 THEN '150-159'
		WHEN A.SYSBP >= 160 AND A.SYSBP < 170 THEN '160-169'
		WHEN A.SYSBP >= 170 AND A.SYSBP <= 180 THEN '170-179'
        WHEN A.SYSBP > 180 THEN '>180'
        WHEN A.SYSBP IS NULL THEN '缺失'
    END AS AgeRange,
    CASE
        WHEN A.SYSBP <= 120  THEN 0
        WHEN A.SYSBP > 120 AND A.SYSBP < 130 THEN 1
        WHEN A.SYSBP >=130 AND A.SYSBP < 140 THEN 2
        WHEN A.SYSBP >= 140 AND A.SYSBP < 150 THEN 3
		WHEN A.SYSBP >= 150 AND A.SYSBP < 160 THEN 4
		WHEN A.SYSBP >= 160 AND A.SYSBP < 170 THEN 5
		WHEN A.SYSBP >= 170 AND A.SYSBP <= 180 THEN 6
        WHEN A.SYSBP > 180 THEN 7
        WHEN A.SYSBP IS NULL THEN 8
    END AS AgeRange1,A.SITEID,B.SITEID, A.SITENM, B.COHORT  
FROM IE as B
LEFT JOIN (
select * from(select l.*,row_number() over (partition by l.SUBJID order by l.PAGEFSDT desc) x from VS l
WHERE l.VSPERF = 1) a where x = 1
)A ON A.SUBJID = B.SUBJID where B.IEYN <> 2
GROUP BY AgeRange,AgeRange1,A.SITEID,B.SITEID, A.SITENM, B.COHORT
ORDER BY AgeRange1;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO site_count, AgeRange_val, AgeRange1_val, siteid_val,siteid1_val, sitenm_val, COHORT_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;

        -- 重置变量
	 
        IF COHORT_val = 1 THEN
            SET COHORT1_val = 'A';
        ELSE
            SET COHORT1_val = 'B';
        END IF;
        
        if siteid_val is null then
          set siteid_val=siteid1_val;
        end if ;
        

        -- 插入数据到 board_t 表中
        INSERT INTO board_t (
            sitename, 
            siteid, 
            cohort, 
            SYSBP_txt,
            SYSBP_rownum,
			SYSBP_count
			)
        VALUES (
            sitenm_val, 
            siteid_val, 
            COHORT1_val,
            AgeRange_val,
            AgeRange1_val,
            site_count);
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_UACR $$
CREATE PROCEDURE `process_data_board_UACR`()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE siteid_val INT;
    DECLARE siteid1_val INT;
    DECLARE sitenm_val VARCHAR(255);
    DECLARE sitenm1_val VARCHAR(255);
    DECLARE COHORT_val VARCHAR(255);
    DECLARE COHORT1_val VARCHAR(255);
    DECLARE AgeRange_val VARCHAR(255);
    DECLARE site_count INT;
    DECLARE AgeRange1_val INT;
	
    DECLARE cur CURSOR FOR 
    /*SELECT COUNT(*) AS count,
    CASE 
        WHEN LBORRES6 = '' OR LBORRES6 IS NULL THEN '缺失'
        WHEN LBORRES6 <= 200 THEN '<=200'
        WHEN LBORRES6 >= 200 AND LBORRES6 < 300 THEN '200-299'
        WHEN LBORRES6 >= 300 AND LBORRES6 < 500 THEN '300-499'
        WHEN LBORRES6 >= 500 AND LBORRES6 < 1000 THEN '500-999'
        WHEN LBORRES6 >= 1000 AND LBORRES6 < 2000 THEN '1000-1999'
        WHEN LBORRES6 >= 2000 AND LBORRES6 < 3000 THEN '2000-2999'
        WHEN LBORRES6 >= 3000 AND LBORRES6 < 5000 THEN '3000-4999'
        WHEN LBORRES6 >= 5000 THEN '>=5000'
    END AS AgeRange,
    CASE 
        WHEN LBORRES6 = '' OR LBORRES6 IS NULL THEN 9
        WHEN LBORRES6 <= 200 THEN 1
        WHEN LBORRES6 >= 200 AND LBORRES6 < 300 THEN 2
        WHEN LBORRES6 >= 300 AND LBORRES6 < 500 THEN 3
        WHEN LBORRES6 >= 500 AND LBORRES6 < 1000 THEN 4
        WHEN LBORRES6 >= 1000 AND LBORRES6 < 2000 THEN 5
        WHEN LBORRES6 >= 2000 AND LBORRES6 < 3000 THEN 6
        WHEN LBORRES6 >= 3000 AND LBORRES6 < 5000 THEN 7
        WHEN LBORRES6 >= 5000 THEN 8
    END AS AgeRange1
FROM LBURI1
WHERE LBTEST8 = 5
GROUP BY AgeRange,AgeRange1
ORDER BY AgeRange1;

SELECT COUNT(B.SUBJID) AS count,
CASE 
        WHEN  A.LBORRES6 > 0 and  A.LBORRES6 < 30 THEN '0-29'
        WHEN  A.LBORRES6 >= 30 AND  A.LBORRES6 < 200 THEN '30-199'
        WHEN  A.LBORRES6 >= 200 AND  A.LBORRES6 < 299 THEN '200-299'
        WHEN  A.LBORRES6 >= 300 AND  A.LBORRES6 < 500 THEN '300-499'
        WHEN  A.LBORRES6 >= 500 AND  A.LBORRES6 < 700 THEN '500-699'
        WHEN  A.LBORRES6 >= 700 AND  A.LBORRES6 < 2000 THEN '700-1999'
        WHEN  A.LBORRES6 >= 2000 AND   A.LBORRES6 < 5000 THEN '2000-4999'
        WHEN  A.LBORRES6 >= 5000 THEN '>=5000'
         WHEN  A.LBORRES6 = '' OR  A.LBORRES6 IS NULL THEN '缺失'
    END AS AgeRange,
    CASE 
        WHEN  A.LBORRES6 > 0 and  A.LBORRES6 < 30 THEN 1
        WHEN  A.LBORRES6 >= 30 AND  A.LBORRES6 < 200 THEN 2
        WHEN  A.LBORRES6 >= 200 AND  A.LBORRES6 < 299 THEN 3
        WHEN  A.LBORRES6 >= 300 AND  A.LBORRES6 < 500 THEN 4
        WHEN  A.LBORRES6 >= 500 AND  A.LBORRES6 < 700 THEN 5
        WHEN  A.LBORRES6 >= 700 AND  A.LBORRES6 < 2000 THEN 6
        WHEN  A.LBORRES6 >= 2000 AND  A.LBORRES6 < 5000 THEN 7
        WHEN  A.LBORRES6 >= 5000 THEN 8
        WHEN  A.LBORRES6 = '' OR  A.LBORRES6 IS NULL THEN 9
    END AS AgeRange1, A.SITEID,B.SITEID, A.SITENM, B.COHORT
 FROM IE as B
LEFT JOIN (
select * from(select l.*,row_number() over (partition by l.SUBJID order by l.PAGEFSDT desc) x from LBURI1 l
WHERE l.LBTEST8 = 5) a where x = 1
) as A ON A.SUBJID = B.SUBJID where B.IEYN <> '2'
GROUP BY AgeRange,AgeRange1, A.SITEID,B.SITEID, A.SITENM, B.COHORT
ORDER BY AgeRange1;
*/

select COUNT(B.SUBJID),
CASE 
        WHEN  A.jc_cnt > 0 and  A.jc_cnt < 30 THEN '0-29'
        WHEN  A.jc_cnt >= 30 AND  A.jc_cnt < 200 THEN '30-199'
        WHEN  A.jc_cnt >= 200 AND  A.jc_cnt < 299 THEN '200-299'
        WHEN  A.jc_cnt >= 300 AND  A.jc_cnt < 500 THEN '300-499'
        WHEN  A.jc_cnt >= 500 AND  A.jc_cnt < 700 THEN '500-699'
        WHEN  A.jc_cnt >= 700 AND  A.jc_cnt < 2000 THEN '700-1999'
        WHEN  A.jc_cnt >= 2000 AND   A.jc_cnt < 5000 THEN '2000-4999'
        WHEN  A.jc_cnt >= 5000 THEN '>=5000'
         WHEN  A.jc_cnt = '' OR  A.jc_cnt IS NULL THEN '缺失'
    END AS AgeRange,
    CASE 
        WHEN  A.jc_cnt > 0 and  A.jc_cnt < 30 THEN 0
        WHEN  A.jc_cnt >= 30 AND  A.jc_cnt < 200 THEN 1
        WHEN  A.jc_cnt >= 200 AND  A.jc_cnt < 299 THEN 2
        WHEN  A.jc_cnt >= 300 AND  A.jc_cnt < 500 THEN 3
        WHEN  A.jc_cnt >= 500 AND  A.jc_cnt < 700 THEN 4
        WHEN  A.jc_cnt >= 700 AND  A.jc_cnt < 2000 THEN 5
        WHEN  A.jc_cnt >= 2000 AND  A.jc_cnt < 5000 THEN 6
        WHEN  A.jc_cnt >= 5000 THEN 7
        WHEN  A.jc_cnt = '' OR  A.jc_cnt IS NULL THEN 8
    END AS AgeRange1, A.SITEID,B.SITEID, A.SITENM, B.SITENM, B.COHORT
FROM IE as B
LEFT JOIN (
select * from(select l.*,row_number() over (partition by l.SUBJID ) x from jc_t l
WHERE l.jc_type = 'UACR') a where x = 1
) as A ON A.SUBJID = B.SUBJID where B.IEYN <> '2'
GROUP BY AgeRange,AgeRange1, A.SITEID,B.SITEID, A.SITENM,B.SITENM, B.COHORT
ORDER BY AgeRange1;



    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO site_count, AgeRange_val, AgeRange1_val, siteid_val,siteid1_val, sitenm_val,sitenm1_val, COHORT_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;

        -- 重置变量
        
        if 	AgeRange_val is null then
        	set AgeRange_val = '缺失';	
        	set AgeRange1_val = 8;
		end if;		     
		     
        IF COHORT_val = 1 THEN
            SET COHORT1_val = 'A';
        ELSE
            SET COHORT1_val = 'B';
        END IF;
		
		 if siteid_val is null then
          set siteid_val=siteid1_val;
          set sitenm_val=sitenm1_val;
        end if ;

        -- 插入数据到 board_t 表中
        INSERT INTO board_t (
            sitename, 
            siteid, 
            cohort, 
            UACR_txt,
            UACR_count,
            UACR_row
           )
        VALUES (
            sitenm_val, 
            siteid_val, 
            COHORT1_val,
            AgeRange_val,
            site_count,
            AgeRange1_val);
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_UACR_jc $$
CREATE PROCEDURE `process_data_board_UACR_jc`()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE SUBJID_val VARCHAR(255);
    DECLARE siteid_val VARCHAR(255);
    DECLARE SITENM_val VARCHAR(255);
    DECLARE COHORT_val VARCHAR(255);
    DECLARE COHORT1_val VARCHAR(255);
    DECLARE LBORRES6_val VARCHAR(255);
    DECLARE LBUORRESU1_val VARCHAR(255);
    DECLARE LBUORRESU1_TXT_val VARCHAR(255);
    DECLARE PAGEFSDT_val VARCHAR(255);

    DECLARE cur CURSOR FOR
        SELECT B.SUBJID, B.SITEID, B.SITENM, B.COHORT, A.LBORRES6, A.LBUORRESU1, A.LBUORRESU1_TXT,A.PAGEFSDT
        FROM IE as B
        LEFT JOIN (
            SELECT l.*, ROW_NUMBER() OVER (PARTITION BY l.SUBJID ORDER BY l.PAGEFSDT DESC) x
            FROM LBURI1 l
            WHERE l.LBTEST8 = 4
        ) A ON A.SUBJID = B.SUBJID and A.LBORRES6 > 0
        WHERE B.IEYN <> '2' AND A.x = 1;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO SUBJID_val, siteid_val, SITENM_val, COHORT_val, LBORRES6_val, LBUORRESU1_val, LBUORRESU1_TXT_val,PAGEFSDT_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;

        -- 处理 LBORRES6_val 为空或 NULL 的情况
       
        -- 根据 cohort 设置 cohort1
        IF COHORT_val = '1' THEN
            SET COHORT1_val = 'A';
        ELSE
            SET COHORT1_val = 'B';
        END IF;

        -- 处理 LBUORRESU1_val 逻辑
        if LBUORRESU1_TXT_val is not null or LBUORRESU1_TXT_val<> '' then
	        if LBUORRESU1_TXT_val = 'mg/mmol' then
	           SET LBORRES6_val = LBORRES6_val*10;
	        end if;
	     end if;
        
        IF LBORRES6_val IS NOT NULL AND (LBORRES6_val < 10) THEN
            SET LBORRES6_val = LBORRES6_val * 1000;
        END IF;
     

        -- 插入数据到 jc_t 表中
        INSERT INTO jc_t (
            subjid,
            siteid,
            sitenm,
            cohort,
            jc_type,
            jc_name,
            jc_cnt,
            jc_dt
        )
        VALUES (
            SUBJID_val, siteid_val, SITENM_val, COHORT1_val, 'UACR', LBUORRESU1_val, LBORRES6_val,PAGEFSDT_val
        );
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_UPCR $$
CREATE PROCEDURE `process_data_board_UPCR`()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE siteid_val INT;
    DECLARE siteid1_val INT;
    DECLARE sitenm_val VARCHAR(255);
    DECLARE sitenm1_val VARCHAR(255);
    DECLARE COHORT_val VARCHAR(255);
    DECLARE COHORT1_val VARCHAR(255);
    DECLARE AgeRange_val VARCHAR(255);
    DECLARE site_count INT;
    DECLARE AgeRange1_val INT;
	
    DECLARE cur CURSOR FOR 
    
    /*
    SELECT COUNT(B.SUBJID) AS count,
    CASE 
        WHEN A.LBORRES6  = '' OR A.LBORRES6 IS NULL THEN '缺失值'
        WHEN A.LBORRES6 < 400  THEN '<400'
        WHEN A.LBORRES6 >= 400 AND A.LBORRES6 < 500 THEN '400-499'
        WHEN A.LBORRES6 >=500 AND A.LBORRES6 < 800 THEN '500-799'
        WHEN A.LBORRES6 >= 800 AND A.LBORRES6 < 1600 THEN '800-1599 '
	    WHEN A.LBORRES6 >= 1600 AND A.LBORRES6 < 3200 THEN '1600-3199'
	    WHEN A.LBORRES6 >= 3200 AND A.LBORRES6 < 4500 THEN '3200-4499'
		WHEN A.LBORRES6 >= 4500 AND A.LBORRES6 < 8000 THEN '4500-7999'
		WHEN A.LBORRES6 >=8000 THEN '>=8000'
	    END AS AgeRange,
    CASE 
        WHEN A.LBORRES6  = '' OR A.LBORRES6 IS NULL THEN 9
        WHEN A.LBORRES6 < 400  THEN 1
        WHEN A.LBORRES6 >= 400 AND A.LBORRES6 < 500 THEN 2
        WHEN A.LBORRES6 >=500 AND A.LBORRES6 < 800 THEN 3
        WHEN A.LBORRES6 >= 800 AND A.LBORRES6 < 1600 THEN 4
	    WHEN A.LBORRES6 >= 1600 AND A.LBORRES6 < 3200 THEN 5
	    WHEN A.LBORRES6 >= 3200 AND A.LBORRES6 < 4500 THEN 6
		WHEN A.LBORRES6 >= 4500 AND A.LBORRES6 < 8000 THEN 7
		WHEN A.LBORRES6 >=8000 THEN 8    
		END AS AgeRange1, A.SITEID, A.SITENM, B.COHORT
FROM  IE as B LEFT JOIN LBURI1 as A ON A.subjid = B.subjid 
WHERE A.LBTEST8 = 4
GROUP BY AgeRange,AgeRange1, A.SITEID, A.SITENM, B.COHORT
ORDER BY AgeRange1;


SELECT COUNT(B.SUBJID) AS count,
CASE 
        
        WHEN A.jc_cnt > 0  and A.jc_cnt < 150 THEN '0-149'
        WHEN A.jc_cnt >= 150 AND A.jc_cnt < 500 THEN '150-499'
        WHEN A.jc_cnt >=500 AND A.jc_cnt < 649 THEN '500-649'
        WHEN A.jc_cnt >= 500 AND A.jc_cnt < 1000 THEN '500-999 '
	    WHEN A.jc_cnt >= 1000 AND A.jc_cnt < 1500 THEN '1000-1499'
	    WHEN A.jc_cnt >= 1500 AND A.jc_cnt < 3500 THEN '1500-3499'
		WHEN A.jc_cnt >= 3500 AND A.jc_cnt < 8000 THEN '3500-7999'
		WHEN A.jc_cnt >=8000 THEN '>=8000'
		WHEN A.jc_cnt  = '' OR A.jc_cnt IS NULL THEN '缺失'
	    END AS AgeRange,
    CASE 
        WHEN A.LBORRES6 > 0  and A.LBORRES6 < 150 THEN 1
        WHEN A.LBORRES6 >= 150 AND A.LBORRES6 < 500 THEN 2
        WHEN A.LBORRES6 >=500 AND A.LBORRES6 < 649 THEN 3
        WHEN A.LBORRES6 >= 500 AND A.LBORRES6 < 1000 THEN 4
	    WHEN A.LBORRES6 >= 1000 AND A.LBORRES6 < 1500 THEN 5
	    WHEN A.LBORRES6 >= 1500 AND A.LBORRES6 < 3500 THEN 6
		WHEN A.LBORRES6 >= 3500 AND A.LBORRES6 < 8000 THEN 7
		WHEN A.LBORRES6 >=8000 THEN 8
		WHEN A.LBORRES6  = '' OR A.LBORRES6 IS NULL THEN 9
		END AS AgeRange1, A.SITEID,B.SITEID, A.SITENM, B.COHORT
 FROM IE as B
LEFT JOIN (
select * from(select l.*,row_number() over (partition by l.SUBJID order by l.PAGEFSDT desc) x from LBURI1 l
WHERE l.LBTEST8 = 4) a where x = 1
) as A ON A.SUBJID = B.SUBJID where B.IEYN <> '2'
GROUP BY AgeRange,AgeRange1, A.SITEID,B.SITEID, A.SITENM, B.COHORT
ORDER BY AgeRange1;


select COUNT(A.SUBJID),
CASE 
        WHEN A.jc_cnt > 0  and A.jc_cnt < 150 THEN '0-149'
        WHEN A.jc_cnt >= 150 AND A.jc_cnt < 500 THEN '150-499'
        WHEN A.jc_cnt >=500 AND A.jc_cnt < 649 THEN '500-649'
        WHEN A.jc_cnt >= 500 AND A.jc_cnt < 1000 THEN '500-999 '
	    WHEN A.jc_cnt >= 1000 AND A.jc_cnt < 1500 THEN '1000-1499'
	    WHEN A.jc_cnt >= 1500 AND A.jc_cnt < 3500 THEN '1500-3499'
		WHEN A.jc_cnt >= 3500 AND A.jc_cnt < 8000 THEN '3500-7999'
		WHEN A.jc_cnt >=8000 THEN '>=8000'
		WHEN A.jc_cnt  = '' OR A.jc_cnt IS NULL THEN '缺失'
	    END AS AgeRange,
    CASE 
        WHEN A.jc_cnt > 0  and A.jc_cnt < 150 THEN 1
        WHEN A.jc_cnt >= 150 AND A.jc_cnt < 500 THEN 2
        WHEN A.jc_cnt >=500 AND A.jc_cnt < 649 THEN 3
        WHEN A.jc_cnt >= 500 AND A.jc_cnt < 1000 THEN 4
	    WHEN A.jc_cnt >= 1000 AND A.jc_cnt < 1500 THEN 5
	    WHEN A.jc_cnt >= 1500 AND A.jc_cnt < 3500 THEN 6
		WHEN A.jc_cnt >= 3500 AND A.jc_cnt < 8000 THEN 7
		WHEN A.jc_cnt >=8000 THEN 8
		WHEN A.jc_cnt  = '' OR A.jc_cnt IS NULL THEN 9
		END AS AgeRange1, A.SITEID,B.SITEID, A.SITENM, B.COHORT
FROM IE as B
LEFT JOIN (
select * from(select l.*,row_number() over (partition by l.SUBJID ) x from jc_t l
WHERE l.jc_type = 'UPCR') a where x = 1
) as A ON A.SUBJID = B.SUBJID where B.IEYN <> '2'
GROUP BY AgeRange,AgeRange1, A.SITEID,B.SITEID, A.SITENM, B.COHORT
ORDER BY AgeRange1;*/

select COUNT(B.SUBJID), 
CASE 
        WHEN A.jc_cnt > 0  and A.jc_cnt < 150 THEN '0-149'
        WHEN A.jc_cnt >= 150 AND A.jc_cnt < 500 THEN '150-499'
        WHEN A.jc_cnt >=500 AND A.jc_cnt < 649 THEN '500-649'
        WHEN A.jc_cnt >= 500 AND A.jc_cnt < 1000 THEN '500-999'
	    WHEN A.jc_cnt >= 1000 AND A.jc_cnt < 1500 THEN '1000-1499'
	    WHEN A.jc_cnt >= 1500 AND A.jc_cnt < 3500 THEN '1500-3499'
		WHEN A.jc_cnt >= 3500 AND A.jc_cnt < 8000 THEN '3500-7999'
		WHEN A.jc_cnt >=8000 THEN '>=8000'
		WHEN A.jc_cnt  = '' OR A.jc_cnt IS NULL THEN '缺失'
	    END AS AgeRange,
    CASE 
        WHEN A.jc_cnt > 0  and A.jc_cnt < 150 THEN 0
        WHEN A.jc_cnt >= 150 AND A.jc_cnt < 500 THEN 1
        WHEN A.jc_cnt >=500 AND A.jc_cnt < 649 THEN 2
        WHEN A.jc_cnt >= 500 AND A.jc_cnt < 1000 THEN 3
	    WHEN A.jc_cnt >= 1000 AND A.jc_cnt < 1500 THEN 4
	    WHEN A.jc_cnt >= 1500 AND A.jc_cnt < 3500 THEN 5
		WHEN A.jc_cnt >= 3500 AND A.jc_cnt < 8000 THEN 6
		WHEN A.jc_cnt >=8000 THEN 7
		WHEN A.jc_cnt  = '' OR A.jc_cnt IS NULL THEN 8
		END AS AgeRange1, A.SITEID,B.SITEID, A.SITENM,B.SITENM,B.COHORT
FROM IE as B
LEFT JOIN (
select * from(select l.*,row_number() over (partition by l.SUBJID ) x from jc_t l
WHERE l.jc_type = 'UPCR') a where x = 1
) as A ON A.SUBJID = B.SUBJID where B.IEYN <> '2'
GROUP BY  AgeRange,AgeRange1,A.SITEID,B.SITEID, A.SITENM, B.SITENM,B.COHORT
ORDER BY AgeRange1;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO site_count, AgeRange_val, AgeRange1_val, siteid_val, siteid1_val, sitenm_val,sitenm1_val,COHORT_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;

        -- 重置变量
        		
				     
		     
        IF COHORT_val = 1 THEN
            SET COHORT1_val = 'A';
        ELSE
            SET COHORT1_val = 'B';
        END IF;
        
        if siteid_val is null then
          set siteid_val=siteid1_val;
          set sitenm_val= sitenm1_val;
        end if ;
	    
	    if 	AgeRange_val is null then
        	set AgeRange_val = '缺失';	
        	set AgeRange1_val = 8;
		end if;		
        -- 插入数据到 board_t 表中
        INSERT INTO board_t (
            sitename, 
            siteid, 
            cohort, 
            UPCR_txt,
            UPCR_count,
            UPCR_row
           )
        VALUES (
            sitenm_val, 
            siteid_val, 
            COHORT1_val,
            AgeRange_val,
            site_count,
            AgeRange1_val
            );
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_UPCR_jc $$
CREATE PROCEDURE `process_data_board_UPCR_jc`()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE SUBJID_val VARCHAR(255);
    DECLARE siteid_val VARCHAR(255);
    DECLARE SITENM_val VARCHAR(255);
    DECLARE COHORT_val VARCHAR(255);
    DECLARE COHORT1_val VARCHAR(255);
    DECLARE LBORRES6_val VARCHAR(255);
    DECLARE LBUORRESU1_val VARCHAR(255);
    DECLARE LBUORRESU1_TXT_val VARCHAR(255);
    DECLARE PAGEFSDT_val VARCHAR(255);

    DECLARE cur CURSOR FOR
        SELECT B.SUBJID, B.SITEID, B.SITENM, B.COHORT, A.LBORRES6, A.LBUORRESU1, A.LBUORRESU1_TXT,A.PAGEFSDT
        FROM IE as B
        LEFT JOIN (
            SELECT l.*, ROW_NUMBER() OVER (PARTITION BY l.SUBJID ORDER BY l.PAGEFSDT DESC) x
            FROM LBURI1 l
            WHERE l.LBTEST8 = 5
        ) A ON A.SUBJID = B.SUBJID
        WHERE B.IEYN <> '2' AND A.x = 1;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO SUBJID_val, siteid_val, SITENM_val, COHORT_val, LBORRES6_val, LBUORRESU1_val, LBUORRESU1_TXT_val,PAGEFSDT_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;

        -- 处理 LBORRES6_val 为空或 NULL 的情况
       
        -- 根据 cohort 设置 cohort1
        IF COHORT_val = '1' THEN
            SET COHORT1_val = 'A';
        ELSE
            SET COHORT1_val = 'B';
        END IF;

        -- 处理 LBUORRESU1_val 逻辑
         if LBUORRESU1_TXT_val is not null or LBUORRESU1_TXT_val<> '' then
	        if LBUORRESU1_TXT_val = 'mg/mmol' then
	           SET LBORRES6_val = LBORRES6_val*10;
	        elseif LBUORRESU1_TXT_val = 'mg/L' then
	          SET LBORRES6_val = LBORRES6_val*0.0001;
	        elseif LBUORRESU1_TXT_val = 'g/L' then
	               SET LBORRES6_val = LBORRES6_val * 1000;
	        end if;
	     end if;

        
        IF LBORRES6_val IS NOT NULL AND (LBORRES6_val < 15) THEN
            SET LBORRES6_val = LBORRES6_val * 1000;
        END IF;

        -- 插入数据到 jc_t 表中
        INSERT INTO jc_t (
            subjid,
            siteid,
            sitenm,
            cohort,
            jc_type,
            jc_name,
            jc_cnt,
            jc_dt
        )
        VALUES (
            SUBJID_val, siteid_val, SITENM_val, COHORT1_val, 'UPCR', LBUORRESU1_val, LBORRES6_val,PAGEFSDT_val
        );
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_Update $$
CREATE PROCEDURE `process_data_board_Update`()
BEGIN
    DECLARE done INT DEFAULT FALSE;   
    DECLARE siteid_val INT;
    DECLARE sitenm_val VARCHAR(255);
	DECLARE province_val VARCHAR(255);
	DECLARE COHORT1_val VARCHAR(255);
	DECLARE diqu_val VARCHAR(255);
	DECLARE Asite_val VARCHAR(255);
	DECLARE Bsite_val VARCHAR(255);
       
    DECLARE cur CURSOR FOR 
        SELECT A.siteid,B.province,B.Asite,B.Bsite
        FROM board_t AS A ,  t_site as B where A.siteid=B.siteid ;
        

    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO siteid_val,province_val,Asite_val,Bsite_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;
        
        -- 在这里添加您的逻辑
        
         update board_t set diqu = province_val, Asite = Asite_val , Bsite= Bsite_val where siteid = siteid_val;
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_age $$
CREATE PROCEDURE `process_data_board_age`()
BEGIN
    DECLARE done INT DEFAULT FALSE;   
    DECLARE siteid_val INT;
    DECLARE siteid1_val INT;
    DECLARE sitenm_val VARCHAR(255);
    DECLARE COHORT_val VARCHAR(255);
    DECLARE COHORT1_val VARCHAR(255);
    DECLARE AgeRange_val VARCHAR(255);
    DECLARE AgeRange1_val INT;
    DECLARE site_count INT;

    DECLARE cur CURSOR FOR 
    SELECT 
        COUNT(*),
        CASE 
            WHEN Age >= 18 AND Age < 25 THEN '18-24' 
            WHEN Age >= 25 AND Age < 35 THEN '25-34' 
            WHEN Age >= 35 AND Age < 45 THEN '35-44' 
            WHEN Age >= 45 AND Age < 55 THEN '45-54' 
            WHEN Age >= 55 AND Age < 65 THEN '55-64' 
            WHEN Age >= 65 AND Age < 75 THEN '65-74' 
            WHEN Age >= 75 AND Age < 85 THEN '75-84' 
            WHEN Age > 85 THEN '85' 
            WHEN Age = '' OR Age IS NULL THEN '缺失'
        END AS AgeRang,
        CASE
            WHEN Age >= 18 AND Age < 25 THEN 1 
            WHEN Age >= 25 AND Age < 35 THEN 2
            WHEN Age >= 35 AND Age < 45 THEN 3
            WHEN Age >= 45 AND Age < 55 THEN 4
            WHEN Age >= 55 AND Age < 65 THEN 5 
            WHEN Age >= 65 AND Age < 75 THEN 6 
            WHEN Age >= 75 AND Age < 85 THEN 7
            WHEN Age > 85 THEN 8
            WHEN Age = '' OR Age IS NULL THEN 9
        END AS AgeRange1,
        A.SITEID, 
        B.SITEID,
        A.SITENM, 
        B.COHORT
    FROM IE as B 
    LEFT JOIN DM as A ON A.SUBJID = B.SUBJID where B.IEYN <> '2'
    GROUP BY AgeRang, AgeRange1, A.SITEID,B.SITEID, A.SITENM, B.COHORT
    ORDER BY AgeRange1;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO site_count, AgeRange_val, AgeRange1_val, siteid_val,siteid1_val, sitenm_val, COHORT_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;
        
        -- 重置变量
               
        -- 根据结果和组别设置值
        IF AgeRange_val IS NULL THEN
            SET AgeRange_val = '缺失';
        END IF;
        
        IF COHORT_val = '1' THEN
            SET COHORT1_val = 'A';
        ELSE
            SET COHORT1_val = 'B';
        END IF; 
        if siteid_val is null then
          set siteid_val= siteid1_val;
        end if;

        -- 插入数据到 board_t 表中
        INSERT INTO board_t (sitename, siteid, cohort, age_txt, age_count)
        VALUES (sitenm_val, siteid_val, COHORT1_val, AgeRange_val, site_count);
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_cfsite $$
CREATE PROCEDURE `process_data_board_cfsite`()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE siteid_val INT;
    DECLARE sitenm_val VARCHAR(255);
    DECLARE province_val VARCHAR(255);
    DECLARE Asite_val VARCHAR(255);
    DECLARE Bsite_val VARCHAR(255);
    
	
    DECLARE cur CURSOR FOR select siteid,sitenm,province,Asite,Bsite from t_site; 
    

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur ;

    read_dm_loop: LOOP
        FETCH cur INTO siteid_val,sitenm_val,province_val,Asite_val,Bsite_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;
			update fuhedu set sitenm = sitenm_val,Asite=Asite_val,Bsite=Bsite_val,diqu=province_val where SITEID=siteid_val;
			update fuheduB set sitenm = sitenm_val,Asite=Asite_val,Bsite=Bsite_val,diqu=province_val where SITEID=siteid_val;
        -- 重置变量
           END LOOP read_dm_loop;

    CLOSE cur;
    insert into fuhedu_tj select A.id,A.ICF_dt,A.date,A.grouptext,A.SITEID,A.SITENM,A.diqu,A.Asite,A.Bsite,A.result,B.result from fuhedu as A inner JOIN fuheduB as B ON A.id=B.id;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_condion $$
CREATE PROCEDURE `process_data_board_condion`()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE siteid_val INT;
    DECLARE siteid1_val INT;
    DECLARE sitenm_val VARCHAR(255);
    DECLARE COHORT_val VARCHAR(255);
    DECLARE COHORT1_val VARCHAR(255);
    DECLARE AgeRange_val VARCHAR(255);
    DECLARE site_count INT;
    DECLARE AgeRange1_val INT;
    DECLARE MH2INDC_TXT_val VARCHAR(255);
	DECLARE cur CURSOR FOR  
   SELECT count(B.subjid),
   CASE 
        WHEN  MH2INDC_TXT ='慢性肾小管间质性肾炎' THEN '慢性肾小管间质性肾炎'
        WHEN  MH2INDC_TXT ='慢性肾小球肾炎' THEN '慢性肾小球肾炎'
        WHEN  MH2INDC_TXT ='糖尿病肾病' THEN '糖尿病肾病'
        WHEN  MH2INDC_TXT ='高血压肾病' THEN '高血压肾病'
        WHEN  MH2INDC_TXT ='其他' THEN '其他'
        WHEN  MH2INDC_TXT ='未知' THEN '未知'
        WHEN  MH2INDC_TXT IS NULL THEN '缺失'
    END AS AgeRange,
    CASE 
        WHEN  MH2INDC_TXT ='慢性肾小管间质性肾炎' THEN 1
        WHEN  MH2INDC_TXT ='慢性肾小球肾炎' THEN 2
        WHEN  MH2INDC_TXT ='糖尿病肾病' THEN 3
        WHEN  MH2INDC_TXT ='高血压肾病' THEN 4
        WHEN  MH2INDC_TXT ='其他' THEN 5
        WHEN  MH2INDC_TXT ='未知' THEN 6
        WHEN  MH2INDC_TXT IS NULL THEN 7
    END AS AgeRange1, A.siteid,B.SITEID,B.SITENM,B.COHORT
    FROM IE as B
LEFT JOIN (
select * from(select l.*,row_number() over (partition by l.SUBJID order by l.PAGEFSDT desc) x from MH2 l
WHERE l.MH2INDC_TXT <> '' or l.MH2INDC_TXT is not null) a where x = 1
)A ON A.SUBJID = B.SUBJID where B.IEYN <> '2'
 group by AgeRange,AgeRange1,A.siteid,B.SITEID,B.SITENM,B.COHORT
 order by AgeRange1;  
   
 -- select * from MH2 WHERE MH2INDC_TXT <> '' or MH2INDC_TXT is not null
   
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO site_count,AgeRange_val,AgeRange1_val,siteid_val,siteid1_val, sitenm_val, COHORT_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;

        -- 重置变量
	   IF COHORT_val=1 THEN
           SET COHORT1_val='A';
        ELSE
           SET COHORT1_val='B';
        END IF;
         if siteid_val is null then
          set siteid_val=siteid1_val;
		 end if;
		 if AgeRange_val is null then
		      set AgeRange_val = '缺失';
		      set AgeRange1_val = '7';
		 end if;
        -- 插入数据到 board_t 表中
        INSERT INTO board_t (
            sitename, 
            siteid, 
            cohort, 
            condion,
            condion_cnt,
            condion_row
			)
        VALUES (
            sitenm_val, 
            siteid_val, 
            COHORT1_val,
            AgeRange_val,
            site_count,
            AgeRange1_val
            );
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_eGFR $$
CREATE PROCEDURE `process_data_board_eGFR`()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE siteid_val INT;
    DECLARE siteid1_val INT;
    DECLARE sitenm_val VARCHAR(255);
    DECLARE COHORT_val VARCHAR(255);
    DECLARE COHORT1_val VARCHAR(255);
    DECLARE AgeRange_val VARCHAR(255);
    DECLARE site_count INT;
    DECLARE AgeRange1_val INT;
   
    DECLARE cur CURSOR FOR 
    /* SELECT
    COUNT(distinct(A.subjid)) AS count,
    CASE
        WHEN A.LBORRES = '' or A.LBORRES IS NULL THEN 'eGFR为空'
        WHEN A.LBORRES >= 90 THEN 'G1期'
        WHEN A.LBORRES >= 60 AND A.LBORRES < 90 THEN 'G2期'
        WHEN A.LBORRES >= 45 AND A.LBORRES < 60 THEN 'G3a期'
        WHEN A.LBORRES >= 30 AND A.LBORRES < 45 THEN 'G3b期'
        WHEN A.LBORRES >= 15 AND A.LBORRES < 30 THEN 'G4期'
        WHEN A.LBORRES < 15 THEN 'G5期'
    END AS AgeRange,
    CASE
        WHEN A.LBORRES = '' and A.LBORRES IS NULL THEN 7
        WHEN A.LBORRES >= 90 THEN 1
        WHEN A.LBORRES >= 60 AND A.LBORRES < 90 THEN 2
        WHEN A.LBORRES >= 45 AND A.LBORRES < 60 THEN 3
        WHEN A.LBORRES >= 30 AND A.LBORRES < 45 THEN 4
        WHEN A.LBORRES >= 15 AND A.LBORRES < 30 THEN 5
        WHEN A.LBORRES < 15 THEN 6
    END AS AgeRange1,
    A.SITEID,
    B.SITEID,
    A.SITENM,
    B.COHORT
FROM IE as B
LEFT JOIN LBCKD as A ON A.SUBJID = B.SUBJID AND A.LBTEST3 = 2
GROUP BY AgeRange, AgeRange1, A.SITEID,B.SITEID,A.SITENM, B.COHORT
ORDER BY AgeRange1;*/
   
   
   
   SELECT  COUNT(B.subjid) AS count,
	 CASE
        WHEN A.LBORRES = '' or A.LBORRES IS NULL THEN '缺失'
        WHEN A.LBORRES >= 90 THEN 'G1期'
        WHEN A.LBORRES >= 60 AND A.LBORRES < 90 THEN 'G2期'
        WHEN A.LBORRES >= 45 AND A.LBORRES < 60 THEN 'G3a期'
        WHEN A.LBORRES >= 30 AND A.LBORRES < 45 THEN 'G3b期'
        WHEN A.LBORRES >= 15 AND A.LBORRES < 30 THEN 'G4期'
        WHEN A.LBORRES < 15 THEN 'G5期'
    END AS AgeRange,
    CASE
        WHEN A.LBORRES = '' or A.LBORRES IS NULL THEN 7
        WHEN A.LBORRES >= 90 THEN 1
        WHEN A.LBORRES >= 60 AND A.LBORRES < 90 THEN 2
        WHEN A.LBORRES >= 45 AND A.LBORRES < 60 THEN 3
        WHEN A.LBORRES >= 30 AND A.LBORRES < 45 THEN 4
        WHEN A.LBORRES >= 15 AND A.LBORRES < 30 THEN 5
        WHEN A.LBORRES < 15 THEN 6
    END AS AgeRange1,
    A.SITEID,
    B.SITEID,
    A.SITENM,
    B.COHORT
 FROM IE as B
LEFT JOIN (
select * from(select l.*,row_number() over (partition by l.SUBJID order by l.PAGEFSDT desc) x from LBCKD l
WHERE l.LBTEST3 = 2) a where x = 1
)A ON A.SUBJID = B.SUBJID where B.IEYN <> '2'
GROUP BY AgeRange, AgeRange1, A.SITEID,B.SITEID,A.SITENM, B.COHORT
ORDER BY AgeRange1;


    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO site_count, AgeRange_val, AgeRange1_val, siteid_val,siteid1_val, sitenm_val, COHORT_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;

        -- 重置变量
       
        -- 根据结果和组别设置值
       
        IF COHORT_val = 1 THEN
            SET COHORT1_val = 'A';
        ELSE
            SET COHORT1_val = 'B';
        END IF;
        
        if siteid_val is null then
          set siteid_val= siteid1_val;
        end if;

        -- 插入数据到 board_t 表中
        INSERT INTO board_t (sitename, siteid, cohort, eGFR_txt, eGFR_count)
        VALUES (sitenm_val, siteid_val, COHORT1_val, AgeRange_val,site_count);
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_fuhedu $$
CREATE PROCEDURE `process_data_board_fuhedu`()
BEGIN
    DECLARE done INT DEFAULT FALSE;   
    DECLARE siteid_val VARCHAR(255);
    DECLARE sitenm_val VARCHAR(255);
    DECLARE COHORT_val VARCHAR(255);
    DECLARE result_val VARCHAR(255);
    DECLARE site_count INT;

    DECLARE cur CURSOR FOR 
       /* SELECT A.SITEID, COUNT(A.id) AS count, A.grouptext, B.sitenm, A.result
        FROM  IE as B LEFT JOIN fuhedu as A ON A.id = B.SUBJID where B.IEYN <> '2'
        GROUP BY A.result, A.grouptext, B.sitenm, A.SITEID;*/
        
        select count(*),siteid,grouptext,sitenm,result from fuhedu group by siteid,grouptext,sitenm,result;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO  site_count, siteid_val,COHORT_val, sitenm_val, result_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;
        
        -- 重置变量
               
        -- 根据结果和组别设置值
            
        -- 插入数据到 board_t 表中
        INSERT INTO board_t (sitename, siteid, cohort,fuheduA,fuheduA_count)
        VALUES (sitenm_val,siteid_val,COHORT_val,result_val,site_count);
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_fuheduB $$
CREATE PROCEDURE `process_data_board_fuheduB`()
BEGIN
    DECLARE done INT DEFAULT FALSE;   
    DECLARE siteid_val INT;
    DECLARE sitenm_val VARCHAR(255);
    DECLARE COHORT_val VARCHAR(255);
    DECLARE COHORT1_val VARCHAR(255);
    DECLARE result_val VARCHAR(255);
   
    DECLARE site_count INT;

    DECLARE cur CURSOR FOR 
        /*SELECT A.SITEID, count(B.subjid), B.COHORT, B.sitenm, A.result
        FROM  IE as B inner JOIN fuheduB as A ON A.id = B.subjid where B.IEYN <> '2'
        GROUP BY B.subjid,A.result,B.COHORT, B.sitenm, A.SITEID;
        
        SELECT  count(B.subjid),A.SITEID, A.grouptxt, B.sitenm, A.result
        FROM  IE as B LEFT JOIN fuheduB as A ON A.id = B.subjid where B.IEYN <> '2'
        group by A.SITEID, A.grouptxt, B.sitenm, A.result
        
        select * from IE where ieyn<>'2'        
        select count(A.id),A.SITEID,B.SITENM,A.result,B.COHORT from fuheduB as A inner join IE as B on A.id= B.subjid 
        where B.IEYN <> '2'
        group by A.SITEID,B.SITENM,A.result,B.COHORT;*/
      --   select * from fuheduB
        select count(id),SITEID,SITENM,result,grouptxt from fuheduB group by SITEID,SITENM,result,grouptxt;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO site_count,siteid_val, sitenm_val, result_val,COHORT_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;
        
        -- 重置变量
              -- 根据结果和组别设置值
         

        
        -- 插入数据到 board_t 表中
        INSERT INTO board_t (sitename, siteid, cohort, fuheduB, fuheduB_count)
        VALUES (sitenm_val, siteid_val, COHORT_val, result_val, site_count);
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_runall $$
CREATE PROCEDURE `process_data_board_runall`()
BEGIN
    
    call process_data_board();
    call process_data_board_age();
    call process_data_board_eGFR();
    call process_data_board_fuhedu();
    call process_data_board_fuheduB();
    call process_data_board_Pro();
    call process_data_board_sex();
    call process_data_board_SYSBP();
    call process_data_board_UACR();
    call process_data_board_UPCR();
    call process_data_board_condion();
    call process_data_board_24H();
    call process_data_board_Update();
    
-- INSERT INTO board_t ( allcount, sitename, siteid, COHORT, sex, sex_count, fuheduA, fuheduA_count, fuheduB, fuheduB_count, age_txt, age_count, eGFR_txt, eGFR_count, UACR_txt, UACR_count, UPCR_txt, UPCR_count, SYSBP_txt, SYSBP_count, LBORRES_txt, LBORRES_count, LBORRES3_txt, LBORRES3_count, LBORRES1_txt, LBORRES1_count, condion, condion_cnt, diqu, Asite, Bsite, dt) 
-- VALUES ( NULL, '厦门市第五医院', 13031, 'A', NULL, NULL, NULL, NULL, '绝对不符合', '0', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2024-05-28 00:03:14');

-- INSERT INTO board_t ( allcount, sitename, siteid, COHORT, sex, sex_count, fuheduA, fuheduA_count, fuheduB, fuheduB_count, age_txt, age_count, eGFR_txt, eGFR_count, UACR_txt, UACR_count, UPCR_txt, UPCR_count, SYSBP_txt, SYSBP_count, LBORRES_txt, LBORRES_count, LBORRES3_txt, LBORRES3_count, LBORRES1_txt, LBORRES1_count, condion, condion_cnt, diqu, Asite, Bsite, dt) 
-- VALUES ( NULL, '厦门市第五医院', 13031, 'B', NULL, NULL, NULL, NULL, '绝对不符合', '0', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2024-05-28 00:03:14');

-- INSERT INTO board_t ( `allcount`, `sitename`, `siteid`, `COHORT`, `sex`, `sex_count`, `fuheduA`, `fuheduA_count`, `fuheduB`, `fuheduB_count`, `age_txt`, `age_count`, `eGFR_txt`, `eGFR_count`, `UACR_txt`, `UACR_count`, `UPCR_txt`, `UPCR_count`, `SYSBP_txt`, `SYSBP_count`, `LBORRES_txt`, `LBORRES_count`, `LBORRES3_txt`, `LBORRES3_count`, `LBORRES1_txt`, `LBORRES1_count`, `condion`, `condion_cnt`, `diqu`, `Asite`, `Bsite`, `dt`) 
-- VALUES ( NULL, '东南大学附属中大医院', 13001, 'A', NULL, NULL, '绝对不符合', '0', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '江苏省', '是', '是', '2024-05-28 14:45:36');

-- INSERT INTO board_t ( `allcount`, `sitename`, `siteid`, `COHORT`, `sex`, `sex_count`, `fuheduA`, `fuheduA_count`, `fuheduB`, `fuheduB_count`, `age_txt`, `age_count`, `eGFR_txt`, `eGFR_count`, `UACR_txt`, `UACR_count`, `UPCR_txt`, `UPCR_count`, `SYSBP_txt`, `SYSBP_count`, `LBORRES_txt`, `LBORRES_count`, `LBORRES3_txt`, `LBORRES3_count`, `LBORRES1_txt`, `LBORRES1_count`, `condion`, `condion_cnt`, `diqu`, `Asite`, `Bsite`, `dt`) 
-- VALUES ( NULL, '东南大学附属中大医院', 13001, 'B', NULL, NULL, '绝对不符合', '0', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '江苏省', '是', '是', '2024-05-28 14:45:36');
    END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_sex $$
CREATE PROCEDURE `process_data_board_sex`()
BEGIN
    DECLARE done INT DEFAULT FALSE;   
    DECLARE siteid_val INT;
    DECLARE sitenm_val VARCHAR(255);
	DECLARE COHORT_val VARCHAR(255);
	DECLARE COHORT1_val VARCHAR(255);
	DECLARE sex_val VARCHAR(255);
	DECLARE sex1_val VARCHAR(255);
	DECLARE male_val VARCHAR(255);
	DECLARE site_count INT;
       
    DECLARE cur CURSOR FOR SELECT A.siteid,count(A.subjid),A.SITENM,A.COHORT,B.sex
							FROM IE as A
							LEFT JOIN DM as B ON A.SUBJID = B.SUBJID where A.IEYN <> '2'
							GROUP BY A.siteid,A.sitenm,A.COHORT,B.sex;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN cur;

    read_dm_loop: LOOP
        FETCH cur INTO siteid_val,site_count,sitenm_val,COHORT_val,sex_val;
        IF done THEN
            LEAVE read_dm_loop;
        END IF;
        
        -- 在这里添加您的逻辑
        if sex_val = 1 then 
          set sex1_val='男';
        elseif sex_val=2 then
          set sex1_val='女';
        elseif sex_val is null then
          set sex1_val = '缺失';
        end if;
        
        if COHORT_val=1 then
        	set COHORT1_val ='A';
        else
        	set COHORT1_val ='B';
         end if;      
         
       INSERT INTO  board_t (sitename,siteid,cohort,sex,sex_count) value(sitenm_val,siteid_val,COHORT1_val,sex1_val,site_count);
    END LOOP read_dm_loop;

    CLOSE cur;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_td $$
CREATE PROCEDURE `process_data_board_td`()
BEGIN
    INSERT INTO board_t(
        UACR_td_count,
        siteid,
        sitename,
        cohort,
        UACR_type,
        UACR_td_txt,
        UACR_td_row
    )
    SELECT 
        count(subjid),
        siteid,
        sitenm,
        cohort,
        jc_type,
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
        CASE 
            WHEN jc_type = 'UACR' AND jc_cnt > 0 AND jc_cnt < 30 THEN '1'
            WHEN jc_type = 'UACR' AND jc_cnt >= 30 AND jc_cnt < 200 THEN '2'
            WHEN jc_type = 'UACR' AND jc_cnt >= 200 AND jc_cnt < 299 THEN '3'
            WHEN jc_type = 'UACR' AND jc_cnt >= 300 AND jc_cnt < 500 THEN '4'
            WHEN jc_type = 'UACR' AND jc_cnt >= 500 AND jc_cnt < 700 THEN '5'
            WHEN jc_type = 'UACR' AND jc_cnt >= 700 AND jc_cnt < 2000 THEN '6'
            WHEN jc_type = 'UACR' AND jc_cnt >= 2000 AND jc_cnt < 5000 THEN '7'
            WHEN jc_type = 'UACR' AND jc_cnt >= 5000 THEN '8'
            WHEN jc_type = 'UPCR' AND jc_cnt > 0 AND jc_cnt < 150 THEN '1'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 150 AND jc_cnt < 500 THEN '2'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 500 AND jc_cnt < 650 THEN '3'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 500 AND jc_cnt < 1000 THEN '4'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 1000 AND jc_cnt < 1500 THEN '5'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 1500 AND jc_cnt < 3500 THEN '6'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 3500 AND jc_cnt < 8000 THEN '7'
            WHEN jc_type = 'UPCR' AND jc_cnt >= 8000 THEN '8'
            WHEN jc_type = '24H' AND jc_cnt > 0 AND jc_cnt < 150 THEN '1'
            WHEN jc_type = '24H' AND jc_cnt >= 150 AND jc_cnt < 500 THEN '2'
            WHEN jc_type = '24H' AND jc_cnt >= 500 AND jc_cnt < 650 THEN '3'
            WHEN jc_type = '24H' AND jc_cnt >= 500 AND jc_cnt < 1000 THEN '4'
            WHEN jc_type = '24H' AND jc_cnt >= 1000 AND jc_cnt < 1500 THEN '5'
            WHEN jc_type = '24H' AND jc_cnt >= 1500 AND jc_cnt < 3500 THEN '6'
            WHEN jc_type = '24H' AND jc_cnt >= 3500 AND jc_cnt < 8000 THEN '7'
            WHEN jc_type = '24H' AND jc_cnt >= 8000 THEN '8'
            WHEN jc_cnt = '0' OR jc_cnt IS NULL THEN '9'
        END AS AgeRange1
    FROM jc_t_td2 
    WHERE jc_dt < DATE_SUB(CURDATE(), INTERVAL 4 WEEK)
    GROUP BY siteid, sitenm, cohort, jc_type, AgeRange, AgeRange1
    ORDER BY AgeRange1;

END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_td_1 $$
CREATE PROCEDURE `process_data_board_td_1`()
BEGIN

/*         */  
insert into jc_t_td2 
SELECT * from(
select J.*,row_number() over(partition by SUBJID ORDER BY jc_dt desc) x from jc_t J where jc_type = 'UACR'
) a WHERE x =1;

/*         */
insert into jc_t_td2
SELECT * from(
select J.*,row_number() over(partition by SUBJID ORDER BY jc_dt desc) x from jc_t J where jc_type = 'UPCR'
) a WHERE x =1 
and subjid not in(select SUBJID FROM jc_t_td2);
insert into jc_t_td2
SELECT * from(
select J.*,row_number() over(partition by SUBJID ORDER BY jc_dt desc) x from jc_t J where jc_type = '24H'
) a WHERE x =1 
and subjid not in(select SUBJID FROM jc_t_td2);


/*         */
INSERT INTO jc_t_td2(subjid, siteid, sitenm, cohort, jc_cnt)
SELECT 
    subjid,
    siteid,
    sitenm,
    CASE 
        WHEN cohort = 1 THEN 'A'
        WHEN cohort = 2 THEN 'B'
    END AS AgeRange,
    '0'
FROM (
    SELECT 
        J.*,
        ROW_NUMBER() OVER(PARTITION BY SUBJID) AS x 
    FROM IE J 
    WHERE IEYN <> '2'
) AS a 
WHERE x = 1 
AND subjid NOT IN (SELECT SUBJID FROM jc_t_td2);


/*         */



     END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_td_24H $$
CREATE PROCEDURE `process_data_board_td_24H`(
    IN input_subjid VARCHAR(255), 
    OUT result_count2 INT
)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE subjid_val VARCHAR(255);
    DECLARE siteid_val VARCHAR(255);
    DECLARE sitenm_val VARCHAR(255);
    DECLARE cohort_val VARCHAR(255);
    DECLARE jc_type_val VARCHAR(255);
    DECLARE jc_cnt_val INT;
    DECLARE jc_dt_val DATE;

    -- 初始化 result_count2
    SET result_count2 = -3;

    -- 查询符合条件的记录
    SELECT COUNT(*)
    INTO jc_cnt_val
    FROM jc_t 
    WHERE subjid = input_subjid 
      AND jc_type = '24H' 
      AND jc_cnt > 0;

    -- 根据查询结果设置 result_count2
    IF jc_cnt_val > 0 THEN
        SET result_count2 = jc_cnt_val;
    END IF;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_td_UACR $$
CREATE PROCEDURE `process_data_board_td_UACR`(IN subjid_input VARCHAR(255), OUT result_count INT)
BEGIN
    DECLARE jc_cnt_val INT;

    -- 计算指定 subjid 的记录数
    SELECT COUNT(subjid) INTO jc_cnt_val
    FROM jc_t 
    WHERE subjid = subjid_input 
    AND jc_type = 'UACR' and jc_cnt > '0';


    -- SELECT COUNT(subjid)    FROM jc_t   WHERE subjid = '11'  AND jc_type = 'UACR' and jc_cnt > '0';
    -- 处理结果
    IF jc_cnt_val > 0 THEN
        SET result_count = jc_cnt_val;
    ELSE 
        SET result_count = -1;
    END IF;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_board_td_UPCR $$
CREATE PROCEDURE `process_data_board_td_UPCR`(
    IN input_subjid VARCHAR(255), 
    OUT result_count1 INT
)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE subjid_val VARCHAR(255);
    DECLARE siteid_val VARCHAR(255);
    DECLARE sitenm_val VARCHAR(255);
    DECLARE cohort_val VARCHAR(255);
    DECLARE jc_type_val VARCHAR(255);
    DECLARE jc_cnt_val INT;
    DECLARE jc_dt_val DATE;

    -- 初始化 result_count1
    SET result_count1 = -2;

    -- 查询符合条件的记录
    SELECT COUNT(*)
    INTO jc_cnt_val
    FROM jc_t 
    WHERE subjid = input_subjid 
      AND jc_type = 'UPCR' 
      AND jc_cnt > 0;

    -- 根据查询结果设置 result_count1
    IF jc_cnt_val > 0 THEN
        SET result_count1 = jc_cnt_val;
    END IF;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_diqu $$
CREATE PROCEDURE `process_data_diqu`()
BEGIN
 	update t_site set province= CONCAT(province,'省');
	update t_site set province= Replace(province,'省','市') where province like ('北京%') or province like ('上海%') or province like ('重庆%') or province like ('天津%');
	update t_site set province= Replace(province,'省','自治区') where province like ('内蒙古%');
	update t_site set province= Replace(province,'省','壮族自治区') where province like ('广西%');
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_fuhedu $$
CREATE PROCEDURE `process_data_fuhedu`()
BEGIN
    DECLARE done INT DEFAULT FALSE;   
    DECLARE subjid_val VARCHAR(255);
    DECLARE A5_val VARCHAR(255);
	DECLARE B6_val VARCHAR(255);
	DECLARE C7_val VARCHAR(255);
	DECLARE C71_val VARCHAR(255);
	DECLARE D8_val VARCHAR(255);
	DECLARE E9_val VARCHAR(255);       
	DECLARE F10_val VARCHAR(255);
	DECLARE G11_val VARCHAR(255);
	DECLARE H12_val VARCHAR(255);
	DECLARE I13_val VARCHAR(255);
	DECLARE J14_val VARCHAR(255);
	DECLARE K15_val VARCHAR(255);
	DECLARE L16_val VARCHAR(255);
	DECLARE M17_val VARCHAR(255);
	DECLARE N18_val VARCHAR(255);                
	DECLARE O19_val VARCHAR(255);
	DECLARE P20_val VARCHAR(255);
	-- DECLARE P20_val VARCHAR(255);
    DECLARE result_val VARCHAR(255);
    DECLARE result1_val VARCHAR(255);
    DECLARE SITEID_val VARCHAR(255);
    DECLARE SITENM_val VARCHAR(255);
    DECLARE grouptxt_val VARCHAR(255);
    DECLARE ICF_dt_val VARCHAR(255);
    -- Cursor for selecting subjid from DM table
    DECLARE cur CURSOR FOR SELECT A.id,A.A5,A.B6,A.C7,A.D8,A.E9,A.F10,A.G11,A.H12,A.I13,A.J14,A.K15,A.L16,A.M17,A.N18,A.O19,A.P20,A.result,B.SITEID,B.SITENM,B.COHORT,C.RFICDAT 
    FROM fuhedu as A,IE as B,ICF as C where A.id=B.subjid and A.id=C.subjid;

	DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
	

OPEN cur;

read_dm_loop: LOOP
    FETCH cur INTO subjid_val,A5_val,B6_val,C7_val,D8_val,E9_val,F10_val,G11_val,H12_val,I13_val,J14_val,K15_val,L16_val,M17_val,N18_val,O19_val,P20_val,result_val,SITEID_val,SITENM_val,grouptxt_val,ICF_dt_val;
    IF done THEN
        LEAVE read_dm_loop;
    END IF;
    
        -- 执行您的逻辑
        set result1_val =
        case
					when F10_val='是' or  H12_val='是' or P20_val='是' then '绝对不符合'
          when  A5_val = '是' and  B6_val = '是'  and C7_val = '是'  and D8_val='否' and E9_val='否' and F10_val='否' and G11_val='否' and H12_val='否' and I13_val='否' and J14_val='否' and K15_val='否' and L16_val='否' and M17_val='否' and N18_val='否' and O19_val='否' and P20_val='否' then '完全符合'
          when (A5_val = '否' or  B6_val = '否'  or C7_val = '否' )  or (D8_val='是' or E9_val='是') or (G11_val='是'  or I13_val='是' or J14_val='是' or K15_val='是') or (M17_val='是' or N18_val='是' or O19_val='是') and (F10_val='否'  or H12_val='否' or P20_val='否')   then '低符合'
          
          else '可能符合'
        end;
        
        -- select result1_val;
       if grouptxt_val = 1 then
          set grouptxt_val='A';
       else
          if grouptxt_val = 2 then
           set grouptxt_val='B';
          else
            set grouptxt_val='C';
          end if;
       end if;
          
           update fuhedu set result= result1_val,SITEID= SITEID_val,grouptext=grouptxt_val,ICF_dt=ICF_dt_val,SITENM= SITENM_val where id=subjid_val;
               
    END LOOP read_dm_loop;

CLOSE cur;
  END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_fuheduB $$
CREATE PROCEDURE `process_data_fuheduB`()
BEGIN
    DECLARE done INT DEFAULT FALSE;   
    DECLARE subjid_val VARCHAR(255);
    DECLARE A1_val VARCHAR(255);
	DECLARE B2_val VARCHAR(255);
	DECLARE C3_val VARCHAR(255);
	DECLARE D4_val VARCHAR(255);
	DECLARE E5_val VARCHAR(255);       
	DECLARE F6_val VARCHAR(255);
	DECLARE G7_val VARCHAR(255);
	DECLARE H8_val VARCHAR(255);
	DECLARE I9_val VARCHAR(255);
	DECLARE J10_val VARCHAR(255);
	DECLARE K11_val VARCHAR(255);
	DECLARE L12_val VARCHAR(255);
	DECLARE M13_val VARCHAR(255);
	DECLARE N14_val VARCHAR(255);                
	DECLARE O15_val VARCHAR(255);
	DECLARE P16_val VARCHAR(255);
	DECLARE Q17_val VARCHAR(255);
	DECLARE R18_val VARCHAR(255);
	DECLARE S19_val VARCHAR(255);
	DECLARE T20_val VARCHAR(255);
	DECLARE U21_val VARCHAR(255);
    DECLARE result_val VARCHAR(255);
    DECLARE result1_val VARCHAR(255);
    DECLARE SITEID_val VARCHAR(255);
    DECLARE SITENM_val VARCHAR(255);
    DECLARE grouptxt_val VARCHAR(255);
    DECLARE ICF_dt_val VARCHAR(255);
    -- Cursor for selecting subjid from DM table
    DECLARE cur CURSOR FOR SELECT A.id,A.A1,A.B2,A.C3,A.D4,A.E5,A.F6,A.G7,A.H8,A.I9,A.J10,A.K11,A.L12,A.M13,A.N14,A.O15,A.P16,A.Q17,A.R18,A.S19,A.T20,A.U21,A.result,B.SITEID,B.SITENM,B.COHORT,C.RFICDAT 
    FROM fuheduB as A,IE as B,ICF as C where A.id=B.subjid and A.id=C.subjid;

	DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
	

OPEN cur;

read_dm_loop: LOOP
    FETCH cur INTO subjid_val,A1_val,B2_val,C3_val,D4_val,E5_val,F6_val,G7_val,H8_val,I9_val,J10_val,K11_val,L12_val,M13_val,N14_val,O15_val,P16_val,Q17_val,R18_val,S19_val,T20_val,U21_val,result_val,SITEID_val,SITENM_val,grouptxt_val,ICF_dt_val;
    IF done THEN
        LEAVE read_dm_loop;
    END IF;
    
    
   /* 
    符合度判断梯度：
	完全符合：1，2，3，4，5填写“是”，且6-20填写“否"；
	可能符合：除完全符合和低符合/不符合之外的情况；
	低符合：1，2，3，4，5至少一项填写“否"，或6-20（7a，10，11，12，15，20除外）至少有一项填写“是”；
	绝对不符合：满足7a，10，11，12，15，20其中任何一项。
	*/
	
	-- E130011001,2024-05-13 13:48:33,NULL,是,是,是,否,数据缺失,数据缺失,否,否,否,否,否,否,否,否,否,否,否,否,否,否,低符合
        -- 执行您的逻辑
        set result1_val =
        case
          when (A1_val='是' and B2_val ='是' and C3_val ='是' and D4_val='是' and E5_val='是') and (F6_val='否' and G7_val='否' and H8_val='否' and I9_val='否' and J10_val='否' and K11_val='否' and L12_val='否' and M13_val='否' and N14_val='否' and O15_val='否' and P16_val='否' and Q17_val='否' and R18_val='否' and S19_val='否' and T20_val='否' and U21_val='否')  then '完全符合'
          when (A1_val='否' or B2_val ='否' or C3_val ='否' or D4_val='否' or E5_val='否') or (F6_val='是'  or H8_val='是' or I9_val='是' or J10_val='是'  or L12_val='是'  or N14_val='是' or O15_val='是'  or Q17_val='是' or R18_val='是' or S19_val='是' or T20_val='是') and (G7_val='否' or K11_val='否' or L12_val='否' or P16_val='否' or U21_val = '否')   then '低符合'
          when  G7_val='是' or K11_val='是' or L12_val='是' or P16_val='是' or U21_val = '是' then '绝对不符合'
          else '可能符合'
        end;
        
         -- select subjid_val,result1_val;
          if grouptxt_val=1 then
             set grouptxt_val='A';
           else
             if grouptxt_val=2 then
             	set grouptxt_val='B';
              else
                 set grouptxt_val='C';
             end if;
             
           end if;
          
           update fuheduB  set result= result1_val,SITEID=SITEID_val,grouptxt = grouptxt_val,ICf_dt=ICF_dt_val,SITENM=SITENM_val where id=subjid_val;
               
    END LOOP read_dm_loop;

CLOSE cur;
  END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_jc_all $$
CREATE PROCEDURE `process_data_jc_all`()
BEGIN
    call process_data_board_24H_jc();  
    call process_data_board_UACR_jc();   
    call process_data_board_UPCR_jc();  
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_data_test $$
CREATE PROCEDURE `process_data_test`()
BEGIN
    DECLARE done INT DEFAULT FALSE;   
    DECLARE subjid_val VARCHAR(255);
   
    -- Cursor for selecting subjid from DM table
   -- DECLARE cur CURSOR FOR SELECT SUBJID FROM IE where COHORT=1;
    DECLARE cur CURSOR FOR SELECT SUBJID FROM IE where IEYN <>'2' ;
 /*	DECLARE LBCKDcur CURSOR FOR  SELECT LBCKD.LBORRES FROM LBCKD WHERE LBCKD.SUBJID = subjid_val AND LBCKD.lbtest3 = 2;
 	DECLARE LBURI1cur CURSOR FOR SELECT LBURI1.SUBJID,LBURI1.LBORRES6,LBURI1.LBTEST8 FROM LBURI1  WHERE LBURI1.SUBJID = subjid_val AND LBURI1.lbtest8 IN (4, 5);
 	DECLARE CMcur CURSOR FOR SELECT CM.SUBJID, CM.CMTRT, CM.cmongo, CM.CMSTDAT FROM CM where CM.SUBJID=subjid_val;
 	DECLARE MHcur CURSOR FOR  SELECT MH.SUBJID, MH.MHTERM FROM MH where MH.SUBJID=subjid_val;
 	DECLARE HOcur CURSOR FOR SELECT HO.SUBJID, HO.HOMETHOD_TXT, HO.HOREAS_TXT, HO.HOREASOTH, HO.HOREAS1, HO.HOSTDAT FROM HO where  HO.SUBJID = subjid_val;
 	DECLARE PR2cur CURSOR FOR SELECT PR2.SUBJID, PR2.PR2TRT, PR2.PR2DAT FROM PR2 where PR2.SUBJID=subjid_val;
 	DECLARE lbchemcur CURSOR FOR SELECT LBCHEM.SUBJID, LBCHEM.LBTEST2, LBCHEM.LBORRES, LBCHEM.LBTEST2_TXT FROM LBCHEM WHERE LBCHEM.SUBJID=subjid_val and LBCHEM.LBTEST2 IN (3, 4);
    DECLARE cm2cur CURSOR FOR  SELECT CM.SUBJID, CM.CMTRT, CM.cmongo, CM.CMDSTXT, CM.CMSTDAT FROM CM where CM.SUBJID = subjid_val;
    DECLARE DSTcur CURSOR FOR SELECT DST.SUBJID, DST.dstyn1 FROM DST WHERE DST.SUBJID=subjid_val;*/

   -- DECLARE cur CURSOR FOR SELECT SUBJID FROM DM;

	DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
	

OPEN cur;

read_dm_loop: LOOP
    FETCH cur INTO subjid_val;
    IF done THEN
        LEAVE read_dm_loop;
    END IF;
    
    -- 执行您的逻辑
   INSERT INTO fuhedu (ID,ICF_dt,date) VALUES (subjid_val,'',now());
    
   call process_eGFR(subjid_val);
   call process_UACR(subjid_val);
   call process_yongyao(subjid_val);
   call process_NYHA(subjid_val);
   call process_XS(subjid_val);
   call process_xnsj(subjid_val);
   call process_LBCHEM(subjid_val);
   call process_DST(subjid_val);
    
END LOOP read_dm_loop;

CLOSE cur;
  END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_eGFR $$
CREATE PROCEDURE `process_eGFR`(IN subjid_val VARCHAR(255))
BEGIN
 DECLARE lborres_val VARCHAR(255);
 DECLARE A5_val VARCHAR(255);
 -- SELECT LBCKD.LBORRES into  FROM LBCKD WHERE LBCKD.SUBJID = subjid_val AND LBCKD.lbtest3 = 2;
 -- SELECT a.LBORRES into lborres_val FROM LBCKD a JOIN (SELECT SUBJID, MAX(PAGEFSDT) as max FROM LBCKD GROUP BY SUBJID) b ON b.SUBJID = subjid_val AND b.max = a.PAGEFSDT and a.LBTEST3=2;
-- SELECT a.LBORRES  FROM LBCKD a JOIN (SELECT SUBJID, MAX(PAGEFSDT) as max FROM LBCKD GROUP BY SUBJID) b ON b.SUBJID = 'E130050015' AND b.max = a.PAGEFSDT and a.LBTEST3=2;
 -- select LBORRES into lborres_val from(select l.*,row_number() over (partition by l.SUBJID order by l.PAGEFSDT) x from LBCKD l) as a where x = 1 and SUBJID=subjid_val and LBTEST3=2;
-- select LBORRES into lborres_val from(select l.*,rank() over (partition by l.SUBJID order by l.PAGEFSDT) x from LBCKD l) as a where x = 1 and SUBJID=subjid_val and LBTEST3=2;
 SELECT LBORRES INTO lborres_val FROM (
    SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
    FROM LBCKD l
    WHERE l.SUBJID = subjid_val AND l.LBTEST3 = 2 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
) AS a
WHERE x = 1;

-- SELECT LBORRES INTO lborres_val FROM (SELECT l.*, (SELECT COUNT(*) FROM LBCKD WHERE SUBJID = l.SUBJID AND PAGEFSDT <= l.PAGEFSDT) AS rn FROM LBCKD l) AS sub WHERE rn = 1 AND SUBJID = subjid_val;
  	IF lborres_val IS NOT NULL and lborres_val <> '' THEN
                IF lborres_val >= 20 AND lborres_val < 90 THEN
                   SET A5_val = '是' ;
                elseif lborres_val >= 90 AND lborres_val <= 100 THEN
                     SET A5_val = '近似' ;
                elseif lborres_val > 100 THEN
                	 SET A5_val =  '否';
                END IF;
       ELSE
                 SET A5_val  = '数据缺失' ;
       END IF;
        
       UPDATE fuhedu SET A5 = A5_val WHERE ID = subjid_val;
	  End $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_eGFRB $$
CREATE PROCEDURE `process_eGFRB`(IN subjid_val VARCHAR(255))
BEGIN
    DECLARE lborres_val VARCHAR(255);
    DECLARE A1_val VARCHAR(255);

    -- 查询 LBORRES 值
    SELECT LBORRES INTO lborres_val FROM (
        SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
        FROM LBCKD l
        WHERE l.SUBJID = subjid_val AND l.LBTEST3 = 2 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
    ) AS a
    WHERE x = 1;

    -- 调试信息
   -- SELECT CONCAT('lborres_val: ', lborres_val) AS debug_info;

    -- 根据 lborres_val 的值设置 A1_val
    IF lborres_val IS NOT NULL AND lborres_val <> '' THEN
        IF lborres_val >= 30 AND lborres_val < 90 THEN
            SET A1_val = '是';
        ELSEIF lborres_val >= 90 AND lborres_val <= 100 THEN
            SET A1_val = '近似';
        ELSEIF lborres_val > 100 THEN
            SET A1_val = '否';
        ELSEIF lborres_val< 30 THEN
        	SET A1_val ='是';
        END IF;
    ELSE
        SET A1_val = '数据缺失';
    END IF;

    -- 调试信息
   -- SELECT CONCAT('A1_val: ', A1_val) AS debug_info;

    -- 更新 fuheduB 表
    UPDATE fuheduB SET A1 = A1_val WHERE ID = subjid_val;
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_tnbB $$
CREATE PROCEDURE `process_tnbB`(IN subjid_val VARCHAR(255))
BEGIN
	DECLARE MHTERM1_val VARCHAR(255);
	DECLARE MHTERM2_val VARCHAR(255);
	DECLARE MHTERM3_val VARCHAR(255);
    DECLARE G7_val VARCHAR(255);
    DECLARE H8_val VARCHAR(255);


	 SELECT MHTERM into MHTERM1_val  FROM MH WHERE  MH.MHTERM like '%1型糖尿病%' and MH.subjid = subjid_val LIMIT 1;
	 SELECT LBORRES into MHTERM2_val FROM LBCKD WHERE LBTEST3 = 11 and subjid = subjid_val LIMIT 1;
	 select count(*) into MHTERM3_val from MH where  MHTERM not like '%1型糖尿病%' and MHTERM  like '%糖尿病%' and subjid = subjid_val group by subjid;
	 -- SELECT * FROM LBCKD WHERE LBTEST3 = 11 and subjid = subjid_val;

	 if MHTERM3_val > 0  then
	      	       
	         if MHTERM2_val is not null and MHTERM2_val <> '' then
		         if MHTERM2_val > 10.5 then
		         	SET H8_val = '是';
		         else
		            SET H8_val = '否';
		         end if;
	      else
	      	SET H8_val='否';
	      end if;
	   else
	        set H8_val='否';
	  end if;
	-- SELECT *  FROM MH WHERE  MH.MHTERM like '%1型糖尿病%' and MH.subjid = 'E130010003' LIMIT 1;
  	  IF MHTERM1_val is not null or MHTERM1_val <> '' THEN
  	     if  MHTERM1_val='1型糖尿病' then
  	       SET G7_val = '否';
	  	 else
	     	SET G7_val = '是';  
	  	 end if;
	   else
	     SET G7_val='否';
	   end if;
	     
	   					           
        -- SELECT CONCAT('UPDATE fuheduB SET A1 = ', A1_val, ' WHERE ID = ', subjid_val, ';');

     UPDATE fuheduB SET G7 = G7_val,H8 = H8_val WHERE ID = subjid_val;
   End $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_xjB $$
CREATE PROCEDURE `process_xjB`(IN subjid_val VARCHAR(255))
BEGIN
	DECLARE LBORRES_val VARCHAR(255);
	DECLARE LBORRES1_val VARCHAR(255);
    DECLARE E5_val VARCHAR(255);
    DECLARE F6_val VARCHAR(255);


/*
 SELECT *  FROM (
    SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
    FROM LBCKD l
    WHERE l.SUBJID = 'E130010001' AND l.LBTEST3 = 2 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
) AS a
WHERE x = 1;


SELECT *  FROM (
    SELECT l.*, RANK() OVER (ORDER BY l.LBDAT desc) AS x
    FROM LBCHEM l
    WHERE l.SUBJID =  'E130020005' AND l.LBTEST2 = 20 
) AS a
WHERE x = 1;

*/


/*
SELECT *  FROM (
    SELECT l.*, RANK() OVER (ORDER BY l.LBDAT desc) AS x
    FROM LBCHEM l
    WHERE l.SUBJID ='E130010001' AND l.LBTEST2 = 20 
) AS a
WHERE x = 1;


SELECT *  FROM (
    SELECT l.*, RANK() OVER (ORDER BY l.LBDAT desc) AS x
    FROM LBCHEM l
    WHERE l.SUBJID ='E130020008' AND l.LBTEST2 = 20 AND l.LBDAT >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
) AS a
WHERE x = 1;

E130050011
E130051001
*/


SELECT LBORRES into LBORRES_val  FROM (
    SELECT l.*, RANK() OVER (ORDER BY l.LBDAT desc) AS x
    FROM LBCHEM l
    WHERE l.SUBJID = subjid_val AND l.LBTEST2 = 20 
) AS a
WHERE x = 1 LIMIT 1;


SELECT LBORRES into LBORRES1_val  FROM (
    SELECT l.*, RANK() OVER (ORDER BY l.LBDAT desc) AS x
    FROM LBCHEM l
    WHERE l.SUBJID = subjid_val AND l.LBTEST2 = 20 AND l.LBDAT >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
) AS a
WHERE x = 1 LIMIT 1;





  	  IF LBORRES_val is not null THEN
  	        if  LBORRES_val > 3.5 and LBORRES_val < 4.8  then
	            SET E5_val = '是';
	        ELSEIF LBORRES_val >= 3 and LBORRES_val< 5.5 then
	            SET E5_val = '近似';
	        elseif LBORRES_val < 3 and LBORRES_val > 5.5 then
	            set E5_val = '否';
	        END IF;
	     else
	     
	     	set E5_val = '数据缺失';
	     
	     end if;
	     
	     IF LBORRES1_val is not null and LBORRES1_val<>''THEN
  	        if  LBORRES_val >= 5.5  then
	            SET F6_val = '是';
	        ELSE
	            SET F6_val = '否';
	        END IF;
	     else
	     
	     	set F6_val = '数据缺失';
	        -- select subjid_val;
	     end if;
	     
	     
	   --  select subjid_val,LBORRES1_val,F6_val;
        
        -- SELECT CONCAT('UPDATE fuheduB SET A1 = ', A1_val, ' WHERE ID = ', subjid_val, ';');

     UPDATE fuheduB SET E5 = E5_val,F6 = F6_val  WHERE ID = subjid_val;
   End $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_xnsj $$
CREATE PROCEDURE `process_xnsj`(IN subjid_val VARCHAR(255))
BEGIN
    DECLARE PR1TRT_val VARCHAR(255);
    DECLARE PR2TRT_val VARCHAR(255);
    DECLARE PR3TRT_val VARCHAR(255);
    DECLARE PR4TRT_val VARCHAR(255);
    DECLARE PR5TRT_val VARCHAR(255);
    DECLARE PR6TRT_val VARCHAR(255);
    DECLARE G11_val VARCHAR(255);
    DECLARE H12_val VARCHAR(255);
    DECLARE L16_val VARCHAR(255);
     
   
    -- 查询LBURI1表中的数据并赋值给变量
    SELECT PR1.PR1TRT into PR1TRT_val FROM PR1 where PR1.SUBJID=subjid_val AND PR1DAT not like ('uk') and PR1DAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() and PR1TRT in ('颈动脉手术','冠状动脉搭桥术','经皮冠状动脉介入术','经导管主动脉瓣植入术','瓣膜置换术');
    select MH.MHTERM into PR2TRT_val FROM MH where MH.SUBJID=subjid_val and MHTERM like '%COVID-19%';
    select MH.MHTERM into PR3TRT_val FROM MH where MH.SUBJID=subjid_val and (MHTERM like '%心肌梗死%' or MHTERM like '%心梗%' or MHTERM like '%心绞痛%' or MHTERM like'%脑梗%'  or MHTERM like'%脑溢血%') LIMIT 1 ;
    SELECT PR1.PR1TRT into PR4TRT_val FROM PR1 where PR1.SUBJID=subjid_val and PR1TRT in ('有实体器官移植','骨髓移植史');
    select PR2TRT into  PR5TRT_val from PR2 where SUBJID=subjid_val and FORMOID='PR2' and PR2YN_TXT='是';
    SELECT PR1.PR1TRT into PR6TRT_val FROM PR1 where PR1.SUBJID=subjid_val and PR1TRT='肾移植';
    -- select PR2TRT  FROM PR2 where PR2TRT like '%COVID-19%';
   -- select * from PR2
   
  -- select * from MH
    -- SELECT PR2.PR2TRT FROM PR2 where PR2DAT not like ('uk') and PR2DAT BETWEEN DATE_SUB(NOW(), INTERVAL 3 MONTH) AND NOW() and PR2TRT in ('有实体器官移植,骨髓移植史', '心肌梗死、心绞痛、脑血管事件、颈动脉手术、冠状动脉搭桥术、经皮冠状动脉介入术、经导管主动脉瓣植入术，瓣膜置换术');
    
    

    -- 根据条件判断B6的值
     -- 更新fuhedu表中的数据
     if PR1TRT_val is not null or PR3TRT_val is not null or PR2TRT_val is not null then
      	set	G11_val='是';
     else 
        set G11_val='否';
     end if ;
     
     if PR4TRT_val is not null then
     	set	H12_val = '是';
     else 
     	set	H12_val = '否';
	 end if;    
	 if PR5TRT_val is not null or  PR6TRT_val is not null then 
     	set	L16_val = '是';
     else 
     	set	L16_val = '否';
	 end if;        
        
    UPDATE fuhedu SET G11 = G11_val,H12 = H12_val,L16=L16_val WHERE ID = subjid_val;

END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_xnsjB $$
CREATE PROCEDURE `process_xnsjB`(IN subjid_val VARCHAR(255))
BEGIN
    DECLARE PR1TRT_val VARCHAR(255);
    DECLARE PR2TRT_val VARCHAR(255);
    DECLARE PR3TRT_val VARCHAR(255);
    DECLARE PR4TRT_val VARCHAR(255);
    DECLARE PR5TRT_val VARCHAR(255);
    DECLARE PR6TRT_val VARCHAR(255);
    DECLARE J10_val VARCHAR(255);
    DECLARE P16_val VARCHAR(255);
    DECLARE L12_val VARCHAR(255);
     
   
    -- 查询LBURI1表中的数据并赋值给变量
    SELECT PR1.PR1TRT into PR1TRT_val FROM PR1 where PR1.SUBJID=subjid_val AND PR1DAT not like ('uk') and PR1DAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() and PR1TRT in ('颈动脉手术','冠状动脉搭桥术','经皮冠状动脉介入术','经导管主动脉瓣植入术','瓣膜置换术') LIMIT 1;
   -- select MH.MHTERM into PR2TRT_val FROM MH where MH.SUBJID=subjid_val and MHTERM like '%COVID-19%';
    select MH.MHTERM into PR3TRT_val FROM MH where MH.SUBJID=subjid_val and (MHTERM like '%心肌梗死%' or MHTERM like '%心梗%' or MHTERM like '%心绞痛%' or MHTERM like'%脑梗%'  or MHTERM like'%脑溢血%')  LIMIT 1;
  --  select * FROM MH where  SUBJID='E130221005' and MHTERM like '%心肌梗死%' or MHTERM like '%心梗%' or MHTERM like '%心绞痛%' or MHTERM like'%脑梗%'     LIMIT 1
    
    SELECT PR1.PR1TRT into PR4TRT_val FROM PR1 where PR1.SUBJID=subjid_val and PR1TRT in ('有实体器官移植','骨髓移植史') LIMIT 1;
   -- select PR2TRT into  PR5TRT_val from PR2 where SUBJID=subjid_val and FORMOID='PR2' and PR2YN_TXT='是';
    SELECT PR1.PR1TRT into PR6TRT_val FROM PR1 where PR1.SUBJID=subjid_val and PR1TRT='肾移植' LIMIT 1;
    -- select PR2TRT  FROM PR2 where PR2TRT like '%COVID-19%';
   -- select * from PR2
   
  -- select * from MH
    -- SELECT PR2.PR2TRT FROM PR2 where PR2DAT not like ('uk') and PR2DAT BETWEEN DATE_SUB(NOW(), INTERVAL 3 MONTH) AND NOW() and PR2TRT in ('有实体器官移植,骨髓移植史', '心肌梗死、心绞痛、脑血管事件、颈动脉手术、冠状动脉搭桥术、经皮冠状动脉介入术、经导管主动脉瓣植入术，瓣膜置换术');
    
    

    -- 根据条件判断B6的值
     -- 更新fuhedu表中的数据
     if PR1TRT_val is not null or PR3TRT_val is not null  then
      	set	J10_val='是';
     else 
        set J10_val='否';
     end if ;
     
     if PR4TRT_val is not null or PR6TRT_val is not null then
     	set	P16_val = '是';
     else 
     	set	P16_val = '否';
	 end if;   
	  
	        
    UPDATE fuheduB  SET J10 = J10_val,P16 = P16_val WHERE ID = subjid_val;

END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_xyB $$
CREATE PROCEDURE `process_xyB`(IN subjid_val VARCHAR(255))
BEGIN
	DECLARE SBP_val VARCHAR(255);
    DECLARE C3_val VARCHAR(255);

/*
 SELECT *  FROM (
    SELECT l.*, RANK() OVER (ORDER BY l.PAGEFSDT) AS x
    FROM LBCKD l
    WHERE l.SUBJID = 'E130020005' AND l.LBTEST3 = 2 AND l.PAGEFSDT >= DATE_SUB(NOW(), INTERVAL 4 MONTH)
) AS a
WHERE x = 1;

*/
-- SELECT LBORRES INTO lborres_val FROM (SELECT l.*, (SELECT COUNT(*) FROM LBCKD WHERE SUBJID = l.SUBJID AND PAGEFSDT <= l.PAGEFSDT) AS rn FROM LBCKD l) AS sub WHERE rn = 1 AND SUBJID = subjid_val;

  -- SELECT SYSBP into SBP_val from VS where subjid = subjid_val and SYSBP is not null and SYSBP <>'';
  -- SELECT * from VS where subjid='E130280004'  and SYSBP is not null and SYSBP <>'' group by subjid 
    SELECT SYSBP INTO SBP_val FROM (SELECT l.*, (SELECT COUNT(*) FROM VS WHERE SUBJID = l.SUBJID AND PAGEFSDT <= l.PAGEFSDT) AS rn FROM VS l) AS sub WHERE rn = 1 AND SUBJID = subjid_val and SYSBP is not null and SYSBP <>'';
-- SELECT SYSBP FROM (SELECT l.*, (SELECT COUNT(*) FROM VS WHERE SUBJID = l.SUBJID AND PAGEFSDT <= l.PAGEFSDT) AS rn FROM VS l) AS sub WHERE rn = 1 AND SUBJID = subjid_val;
  	  IF SBP_val is not null THEN
  	        if SBP_val >= 130 then
	            SET C3_val = '是';
	        ELSE
	            SET C3_val = '否';
	        END IF;
	     else
	     
	     	set C3_val = '数据缺失';
	     
	     end if;
	        
        
        -- SELECT CONCAT('UPDATE fuheduB SET A1 = ', A1_val, ' WHERE ID = ', subjid_val, ';');

     UPDATE fuheduB SET C3 = C3_val WHERE ID = subjid_val;
   End $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_yongyao $$
CREATE PROCEDURE `process_yongyao`(IN subjid_val VARCHAR(255))
BEGIN
    DECLARE CMTRT_val int;
    DECLARE CMTRT1_val VARCHAR(255);
    DECLARE CMTRT2_val VARCHAR(255);
    DECLARE CMTRT3_val VARCHAR(255);
    DECLARE CMTRT4_val VARCHAR(255);
    DECLARE CMDSTXT1_val VARCHAR(255);
    DECLARE CMDSTXT2_val VARCHAR(255);
    DECLARE CMDSTXT3_val VARCHAR(255);
    DECLARE CMONGO1_val VARCHAR(255);
    DECLARE CMONGO2_val VARCHAR(255);
    DECLARE CMONGO3_val VARCHAR(255);
    DECLARE C7_val VARCHAR(255);
    DECLARE M17_val VARCHAR(255);
    DECLARE M171_val VARCHAR(255);
    DECLARE M172_val VARCHAR(255);
    DECLARE M173_val VARCHAR(255);
    DECLARE N18_val VARCHAR(255);




    -- 查询LBURI1表中的数据并赋值给变量
   
    
      SELECT  count(*) into CMTRT_val FROM CM where 
      CM.SUBJID=subjid_val 
      and (CM.CMTRT LIKE '%普利%' 
   OR CM.CMTRT LIKE '%利酮%'
   OR CM.CMTRT LIKE '%沙坦%' 
   OR CM.CMTRT LIKE '%螺内酯%'
   OR CM.CMTRT LIKE '%列净%' ) and CMONGO ='1'  group by CM.SUBJID LIMIT 1;
   -- AND CMSTDAT NOT LIKE '%uk%' 
  -- AND CMSTDAT < DATE_SUB(CURDATE(), INTERVAL 4 WEEK) group by SUBJID;
  
  
      
    -- 现在时间-处方时间>=4周 是 else 否
    
     
     /*
     
      SELECT  count(*)  FROM CM where 
      (CM.CMTRT LIKE '%普利%'
   OR CM.CMTRT LIKE '%利酮%'
   OR CM.CMTRT LIKE '%沙坦%' 
   OR CM.CMTRT LIKE '%螺内酯%'
   OR CM.CMTRT LIKE '%列净%' ) and CMONGO ='1'  AND CMSTDAT NOT LIKE '%uk%' 
   AND CMSTDAT < DATE_SUB(CURDATE(), INTERVAL 4 WEEK) group by SUBJID;


 SELECT  count(*) FROM CM where 
      CM.SUBJID='E130051003' 
      and (CM.CMTRT LIKE '%普利%' 
   OR CM.CMTRT LIKE '%利酮%'
   OR CM.CMTRT LIKE '%沙坦%' 
   OR CM.CMTRT LIKE '%螺内酯%'
   OR CM.CMTRT LIKE '%列净%' ) and CMONGO ='1'  group by CM.SUBJID;

     
     
      SELECT  count(*)  FROM CM where 
      CM.CMTRT LIKE '%卡托普利%' 
   OR CM.CMTRT LIKE '%依那普利%' 
   OR CM.CMTRT LIKE '%贝那普利%' 
   OR CM.CMTRT LIKE '%福辛普利%' 
   OR CM.CMTRT LIKE '%雷米普利%' 
   OR CM.CMTRT LIKE '%培哚普利%' 
   OR CM.CMTRT LIKE '%咪达%' 
   OR CM.CMTRT LIKE '%依普利酮或非奈利酮%' 
   OR CM.CMTRT LIKE '%波生坦%' 
   OR CM.CMTRT LIKE '%安立生坦%' 
   OR CM.CMTRT LIKE '%马昔腾坦%' 
   OR CM.CMTRT LIKE '%氯沙坦%' 
   OR CM.CMTRT LIKE '%缬沙坦%' 
   OR CM.CMTRT LIKE '%厄贝沙坦%' 
   OR CM.CMTRT LIKE '%替米沙坦%' 
   OR CM.CMTRT LIKE '%奥美沙坦%' 
   OR CM.CMTRT LIKE '%坎地沙坦%' 
   OR CM.CMTRT LIKE '%螺内酯%' 
   OR CM.CMTRT LIKE '%依普利酮%' 
   OR CM.CMTRT LIKE '%非奈利酮%' and CMONGO ='1' group by SUBJID LIMIT 1;
*/       
      
	  -- SELECT * FROM CM where  CM.CMSTDAT not like('%uk%') AND CM.CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 4 WEEK) AND NOW() and CM.CMTRT in ('卡托普利', '依那普利', '贝那普利', '福辛普利', '雷米普利', '培哚普利', '咪达', '依普利酮或非奈利酮', '达格列净', '恩格列净', '卡格列净', '艾托格列净', '波生坦', '安立生坦', '马昔腾坦');
      SELECT  CM.CMTRT into CMTRT1_val FROM CM where CM.SUBJID=subjid_val and  CM.CMSTDAT not like('%uk%') and CM.CMTRT = '泼尼松'  and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() LIMIT 1;
      SELECT  CM.CMTRT into CMTRT2_val FROM CM where CM.SUBJID=subjid_val and   CM.CMSTDAT not like('%uk%') and CM.CMTRT = '硫唑嘌呤' and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() LIMIT 1;
      SELECT  CM.CMTRT into CMTRT3_val FROM CM where CM.SUBJID=subjid_val and   CM.CMSTDAT not like('%uk%') and CM.CMTRT = '吗替麦考酚酯' and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() LIMIT 1;

       SELECT  CM.CMDSTXT into CMDSTXT1_val FROM CM where CM.SUBJID=subjid_val and  CM.CMSTDAT not like('%uk%') and CM.CMTRT ='泼尼松' and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() LIMIT 1;
       SELECT  CM.CMDSTXT into CMDSTXT2_val FROM CM where CM.SUBJID=subjid_val and  CM.CMSTDAT not like('%uk%') and CM.CMTRT ='硫唑嘌呤' and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() LIMIT 1;
       SELECT  CM.CMDSTXT into CMDSTXT3_val FROM CM where CM.SUBJID=subjid_val and  CM.CMSTDAT not like('%uk%') and CM.CMTRT ='吗替麦考酚酯' and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() LIMIT 1;
       SELECT  CM.CMONGO into CMONGO1_val FROM CM where CM.SUBJID=subjid_val and  CM.CMSTDAT not like('%uk%') and CM.CMTRT ='泼尼松' and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() LIMIT 1;
       SELECT  CM.CMONGO into CMONGO2_val FROM CM where CM.SUBJID=subjid_val and  CM.CMSTDAT not like('%uk%') and CM.CMTRT ='硫唑嘌呤' and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() LIMIT 1;
       SELECT  CM.CMONGO into CMONGO3_val FROM CM where CM.SUBJID=subjid_val and  CM.CMSTDAT not like('%uk%') and CM.CMTRT ='吗替麦考酚酯' and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() LIMIT 1;
       
       SELECT  CM.CMTRT into CMTRT4_val FROM CM where CM.SUBJID=subjid_val and CM.CMSTDAT not like('%uk%') and CM.CMTRT in ('英夫利昔单抗', '伊那西普', '托珠单抗') LIMIT 1;

     -- SELECT  CM.CMTRT FROM CM where  CM.CMSTDAT not like('%uk%') and CM.CMTRT in ('泼尼松', '硫唑嘌呤', '吗替麦考酚酯') and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 1 MONTH) AND NOW();
     -- select * from CM 
                 -- CMSTDAT_val = STR_TO_DATE (CMSTDAT_val_str, '%Y-%m-%d');
          
	        IF CMTRT_val >= 1  THEN
	            SET C7_val = '是';
	        ELSE
	            SET C7_val = '否';
	     	      	           
	     end if;   
	        if CMTRT1_val is not null then
	            if CMDSTXT1_val is not null then
	               if CMDSTXT1_val < 10 and CMONGO1_val =1 then
	                  set M171_val ='是';
	        		else 
	        		  set M171_val='否';
	        		end if;
	        	  else
	        	     set M171_val ='否';
	        	  end if;   
	       else 
	            set M171_val ='否';
	       end if;
	       
	       
	       if CMTRT2_val is not null then
	            if CMDSTXT2_val is not null then
	               if CMDSTXT2_val <= 100 and CMONGO2_val =1 then
	                  set M172_val ='是';
	        		else 
	        		  set M172_val='否';
	        		end if;
	        	  else
	        	     set M172_val ='否';
	        	  end if;   
	       else 
	            set M172_val ='否';
	       end if;

	       if CMTRT3_val is not null then
	            if CMDSTXT3_val is not null then
	               if CMDSTXT3_val <= 1000 and CMONGO3_val =1 then
	                  set M173_val ='是';
	        		else 
	        		  set M173_val='否';
	        		end if;
	        	  else
	        	     set M173_val ='否';
	        	  end if;   
	       else 
	            set M173_val ='否';
	       end if;
	       
	        	  if M171_val ='是' and M172_val ='是' and M173_val ='是' then 
	        	      set M17_val ='是';
	        	  else 
	        	      set M17_val ='否';
	        	  end if;
	        	  
	        if CMTRT4_val is not null then
	           set N18_val='是';
	        else 
	           set N18_val='否';
	        end if;
	        
	   			UPDATE fuhedu SET C7 = C7_val,M17 = M17_val, N18 = N18_val WHERE ID = subjid_val;
    
   
END $$
DELIMITER ;

DELIMITER $$
DROP PROCEDURE IF EXISTS process_yongyaoB $$
CREATE PROCEDURE `process_yongyaoB`(IN subjid_val VARCHAR(255))
BEGIN
    DECLARE CMTRT_val int;
    DECLARE CMTRT1_val int;
    DECLARE CMTRT2_val int;
    DECLARE CMTRT3_val int;
    DECLARE Q17_val VARCHAR(255);
    DECLARE R18_val VARCHAR(255);
    DECLARE S19_val VARCHAR(255);




    -- 查询CM表中的数据并赋值给变量
   
      SELECT  count(*) into CMTRT_val FROM CM where CM.SUBJID=subjid_val 
      and CM.CMTRT in ('氢化可的松','泼尼松','硫唑嘌呤','甲氧蝶呤','环磷酰胺','环孢素','他克莫司','西罗莫司','CD3单克隆抗体(OKT3)','利妥昔单抗','英夫利昔单抗','伊那西普','托珠单抗') 
      and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() and CMONGO <> '1'  group by subjid;
	 
	  SELECT  count(*) into CMTRT1_val FROM CM where CM.SUBJID=subjid_val 
      and CM.CMTRT in ('氢化可的松','泼尼松','硫唑嘌呤','甲氧蝶呤','环磷酰胺','环孢素','他克莫司','西罗莫司','CD3单克隆抗体(OKT3)','利妥昔单抗','英夫利昔单抗','伊那西普','托珠单抗') 
      and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 MONTH) AND NOW() and CMONGO =1 group by subjid;
      
      select count(*)  into CMTRT2_val from  CM where CM.SUBJID=subjid_val
      and CM.CMTRT in ('螺内酯','依普利酮','非奈利酮','氨苯蝶啶或阿米洛利','环硅酸锆钠','patiromer','聚磺苯乙烯钠')
      and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 12 WEEK) AND NOW()  group by subjid;
      
      select count(*)  into CMTRT3_val from  CM where CM.SUBJID=subjid_val
      and CM.CMTRT in ('阿帕他胺','avasimibe','卡马西平','恩扎卢胺','lumacaftor','米托坦','苯妥英','利福平','利福喷丁','圣约翰草')
      group by subjid;

     -- SELECT  count(*)  FROM CM where 
     -- CM.CMTRT in ('氢化可的松','泼尼松','硫唑嘌呤','甲氧蝶呤','环磷酰胺','环孢素','他克莫司','西罗莫司','CD3单克隆抗体(OKT3)','利妥昔单抗','英夫利昔单抗','伊那西普','托珠单抗') 
     -- and CMSTDAT BETWEEN DATE_SUB(NOW(), INTERVAL 3 MONTH) AND NOW() and CMONGO =1 group by subjid;
			
		if CMTRT_val >= 1 then
		    if CMTRT1_val >= 1 then
		    	set Q17_val = '否';
		    else
		       set Q17_val = '是';
		    end if; 
		else
		   	set Q17_val = '否';		    
		end if;
		  
		if CMTRT2_val > 1 then
		    set R18_val = '是';
		else 
		    set R18_val = '否';  
		end if ;
	    
	    if CMTRT3_val > 1 then
	        set  S19_val ='是';
	    else
	        set S19_val='否';
	    end if;
	   	
	   	
	   	
	   	UPDATE fuheduB SET Q17 = Q17_val,R18 = R18_val,S19 = S19_val WHERE ID = subjid_val;
    
   
END $$
DELIMITER ;

