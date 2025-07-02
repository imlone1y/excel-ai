def return_sql():
    return """
/* =========================================================
   產線即時效率查詢（修正版）
   最後一句為 SELECT，適合給 Python 直接抓取結果
   ========================================================= */
SET NOCOUNT ON;               -- ← 關閉 (x rows affected) 訊息

/* ---------- 1. 取得目前時間區段 ---------- */
DECLARE @Now nvarchar(4) =
(
    SELECT
        RIGHT('0' + CAST(DATEPART(HOUR  , GETDATE()) AS nvarchar), 2) +
        RIGHT('0' + CAST(CASE WHEN DATEPART(MINUTE, GETDATE()) < 30
                              THEN 0 ELSE 30 END AS nvarchar), 2)
);

SELECT  CONVERT(varchar(10), GETDATE(), 111) AS today,
        @Now AS nowTime,
        CASE @Now
             WHEN '0730' THEN 0.5 WHEN '0800' THEN 0.5
             WHEN '0830' THEN 1   WHEN '0900' THEN 1.5
             WHEN '0930' THEN 2   WHEN '1000' THEN 2.5
             WHEN '1030' THEN 3   WHEN '1100' THEN 3.5
             WHEN '1130' THEN 4   WHEN '1200' THEN 4.5
             WHEN '1230' THEN 4.5 WHEN '1300' THEN 4.5
             WHEN '1330' THEN 5   WHEN '1400' THEN 5.5
             WHEN '1430' THEN 6   WHEN '1500' THEN 6.5
             WHEN '1530' THEN 7   WHEN '1600' THEN 7.5
             WHEN '1630' THEN 8   WHEN '1700' THEN 8.5
             WHEN '1730' THEN 9   WHEN '1800' THEN 9.5
             WHEN '1830' THEN 10  WHEN '1900' THEN 10
             WHEN '1930' THEN 10.5 WHEN '2000' THEN 11
             WHEN '2030' THEN 11.5 WHEN '2100' THEN 12
             WHEN '2130' THEN 12.5 WHEN '2200' THEN 13
             WHEN '2230' THEN 13.5 WHEN '2300' THEN 14
             WHEN '2330' THEN 14.5 ELSE 0
        END AS workHourNow
INTO #tempTimeNow;


/* ---------- 2. 依 View_WorkTimes 取得各組上班起始時間 ---------- */
SELECT DISTINCT
       workDate     COLLATE Chinese_Taiwan_Stroke_90_BIN AS workDate,
       StdCode      COLLATE Chinese_Taiwan_Stroke_90_BIN AS StdCode,
       onWorkTime,
       onWorkTimeNeedPlus
INTO #tempOnWorkTime
FROM (
    SELECT
        REPLACE(REPLACE(REPLACE(a.DEP_N1,'車縫',''),'-',''),' ','') AS Clean,
        LEFT(REPLACE(REPLACE(REPLACE(a.DEP_N1,'車縫',''),'-',''),' ','') ,1)
          + RIGHT('00' + SUBSTRING(REPLACE(REPLACE(REPLACE(a.DEP_N1,'車縫',''),'-',''),' ','') ,2,10),2) AS StdCode,
        workDate,
        CASE
            WHEN workTime_0730 > TotalEmp80Percent THEN '0730'
            WHEN workTime_0800 > TotalEmp80Percent THEN '0800'
            WHEN workTime_0830 > TotalEmp80Percent THEN '0830'
            WHEN workTime_0900 > TotalEmp80Percent THEN '0900'
            WHEN workTime_0930 > TotalEmp80Percent THEN '0930'
            WHEN workTime_1000 > TotalEmp80Percent THEN '1000'
            WHEN workTime_1030 > TotalEmp80Percent THEN '1030'
            WHEN workTime_1100 > TotalEmp80Percent THEN '1100'
            WHEN workTime_1130 > TotalEmp80Percent THEN '1130'
            WHEN workTime_1200 > TotalEmp80Percent THEN '1200'
            WHEN workTime_1230 > TotalEmp80Percent THEN '1230'
            WHEN workTime_1300 > TotalEmp80Percent THEN '1300'
            WHEN workTime_1330 > TotalEmp80Percent THEN '1330'
            WHEN workTime_1400 > TotalEmp80Percent THEN '1400'
            WHEN workTime_1430 > TotalEmp80Percent THEN '1430'
            WHEN workTime_1500 > TotalEmp80Percent THEN '1500'
        END AS onWorkTime,
        /* 對應加班小時數（0.5、1 …） */
        CASE
            WHEN workTime_0730 > TotalEmp80Percent THEN 0
            WHEN workTime_0800 > TotalEmp80Percent THEN 0.5
            WHEN workTime_0830 > TotalEmp80Percent THEN 1
            WHEN workTime_0900 > TotalEmp80Percent THEN 1.5
            WHEN workTime_0930 > TotalEmp80Percent THEN 2
            WHEN workTime_1000 > TotalEmp80Percent THEN 2.5
            WHEN workTime_1030 > TotalEmp80Percent THEN 3
            WHEN workTime_1100 > TotalEmp80Percent THEN 3.5
            WHEN workTime_1130 > TotalEmp80Percent THEN 4
            WHEN workTime_1200 > TotalEmp80Percent THEN 4.5
            WHEN workTime_1230 > TotalEmp80Percent THEN 4.5
            WHEN workTime_1300 > TotalEmp80Percent THEN 4.5
            WHEN workTime_1330 > TotalEmp80Percent THEN 5
            WHEN workTime_1400 > TotalEmp80Percent THEN 5.5
            WHEN workTime_1430 > TotalEmp80Percent THEN 6
            WHEN workTime_1500 > TotalEmp80Percent THEN 6.5
        END AS onWorkTimeNeedPlus
    FROM [192.168.1.247].[GP8000].[dbo].[View_WorkTimes] AS a
    WHERE DEP_N1 LIKE '車縫%' 
      AND workDate  = CONVERT(varchar(10), GETDATE(), 111)
) AS a;

/* ---------- 3. 計算實際工作秒數 (#tempWorkHours) ---------- */
SELECT a.*,
       b.nowTime,
       b.workHourNow,
       b.workHourNow - a.onWorkTimeNeedPlus AS realworkHourNow
INTO #tempWorkHours
FROM #tempOnWorkTime AS a
LEFT JOIN #tempTimeNow AS b
       ON a.workDate = b.today;


/* ---------- 4. 今日各組人數 / IE 秒 ---------- */
SELECT  REPLACE(A_Line,'-LINE ','')                     AS A_Line,
        B_style,
        CAST(AQ_WorkPersonNum  AS numeric(15,2))        AS AQ_WorkPersonNum,
        CAST(Estimate_ie_Import AS numeric(15,2))       AS Estimate_ie_Import,
        WorkDate
INTO #tempGroupPeople
FROM GGgooleSheetRowData_PeopleHours
WHERE WorkDate = CONVERT(varchar(10), GETDATE(), 111);


/* ---------- 5. 今日車縫下線數量 (#tempTieSeam) ---------- */
SELECT dept_no,
       creator,
       cus_item_no,
       SUM(now_qty)                    AS total_now_qty,
       MAX(offline_date)               AS offline_date
INTO #tempTieSeam
FROM mpsc_tie_seam_status
WHERE CONVERT(varchar(10), offline_date, 111) = CONVERT(varchar(10), GETDATE(), 111)
GROUP BY dept_no, creator, cus_item_no;


/* ---------- 6. 今日瑕疵 & 檢查數 ---------- */
SELECT dept_no, cus_item_no, SUM(defect_qty) AS total_defect_qty
INTO #tempDefect
FROM mpsc_qc_fix_log
WHERE CONVERT(varchar(10), work_date, 111) = CONVERT(varchar(10), GETDATE(), 111)
GROUP BY dept_no, cus_item_no;

SELECT dept_no, cus_item_no, SUM(now_qty) AS chk_now_qty
INTO #tempChkLog
FROM mpsc_qc_chk_log
WHERE CONVERT(varchar(10), work_date, 111) = CONVERT(varchar(10), GETDATE(), 111)
GROUP BY dept_no, cus_item_no;


/* ---------- 7. 產線占比 (#tempGroupPercent) ---------- */
SELECT a.*,
       CAST((a.total_now_qty / b.groupTotal) * 100 AS numeric(15,2)) AS groupPercent
INTO #tempGroupPercent
FROM #tempTieSeam AS a
LEFT JOIN (
    SELECT dept_no, creator, SUM(total_now_qty) AS groupTotal
    FROM #tempTieSeam
    GROUP BY dept_no, creator
) AS b
    ON a.dept_no = b.dept_no AND a.creator = b.creator;


/* ---------- 8. 今日所有款號 (#tempALLTieSeam) ---------- */
SELECT DISTINCT dept_no, creator, cus_item_no
INTO #tempALLTieSeam
FROM mpsc_tie_seam_status
WHERE offline_date IS NULL
  AND CONVERT(varchar(10), online_date, 111) = CONVERT(varchar(10), GETDATE(), 111);


/* ---------- 9. 最終輸出 ---------- */
SELECT 
    a.A_Line                          AS Line,
    a.B_style                         AS Style,
    a.offline_date                    AS Latest_Activity_Time,
    a.total_now_qty                   AS TieSeamQty,
    a.total_defect_qty                AS Defect_Quantity,
    a.net_good_quantity               AS Net_Good_Qty,
    a.defect_rate                     AS DefectRate,
    a.AQ_WorkPersonNum                AS People,
    a.Estimate_ie_Import              AS IE_Seconds,
    CAST(a.workSeconds     AS numeric(15,0)) AS WorkSeconds,
    CAST(a.realWorkSeconds AS numeric(15,2)) AS RealWorkSeconds,
    a.groupPercent                    AS GroupPercent,
    CAST(a.targetNum       AS numeric(15,0)) AS TargetNum,
    CAST(a.efficiency      AS numeric(15,2)) AS Efficiency
FROM (
    SELECT
        gp.A_Line,
        ts.dept_no,
        gp.B_style,
        gp.AQ_WorkPersonNum,
        gp.Estimate_ie_Import,
        gp.WorkDate,
        ts.offline_date,

        ISNULL(ts.total_now_qty, 0)                    AS total_now_qty,
        ISNULL(df.total_defect_qty, 0)                 AS total_defect_qty,
        ISNULL(cl.chk_now_qty, 0)                      AS chk_now_qty,
        ISNULL(ts.total_now_qty, 0) - ISNULL(df.total_defect_qty, 0) AS net_good_quantity,
        CASE
            WHEN cl.chk_now_qty = 0 THEN 0
            ELSE CAST(ISNULL(df.total_defect_qty, 0) * 100.0 / cl.chk_now_qty AS numeric(15,2))
        END                                           AS defect_rate,
        gpct.groupPercent,
        wh.realworkHourNow * 3600                                  AS workSeconds,
        wh.realworkHourNow * 3600 * (gpct.groupPercent / 100.0)    AS realWorkSeconds,
        CASE
            WHEN gp.Estimate_ie_Import = 0 OR gp.AQ_WorkPersonNum = 0 THEN 0
            ELSE (wh.realworkHourNow * 3600 * (gpct.groupPercent / 100.0) * gp.AQ_WorkPersonNum)
                 / gp.Estimate_ie_Import
        END                                           AS targetNum,
        CASE
            WHEN gp.Estimate_ie_Import = 0 OR gp.AQ_WorkPersonNum = 0 THEN 0
            ELSE ISNULL(ts.total_now_qty, 0) * 100.0 /
                 ((wh.realworkHourNow * 3600 * (gpct.groupPercent / 100.0) * gp.AQ_WorkPersonNum) /
                  gp.Estimate_ie_Import)
        END                                           AS efficiency
    FROM #tempGroupPeople AS gp
    LEFT JOIN #tempTieSeam      AS ts  ON gp.A_Line = ts.creator  AND gp.B_style = ts.cus_item_no
    LEFT JOIN #tempDefect       AS df  ON ts.dept_no = df.dept_no AND gp.B_style = df.cus_item_no
    LEFT JOIN #tempChkLog       AS cl  ON ts.dept_no = cl.dept_no AND gp.B_style = cl.cus_item_no
    LEFT JOIN #tempGroupPercent AS gpct ON gp.A_Line = gpct.creator AND gp.B_style = gpct.cus_item_no
    LEFT JOIN #tempWorkHours    AS wh   ON gp.A_Line = wh.StdCode  AND gp.WorkDate = wh.workDate
    WHERE ts.total_now_qty     <> 0
      AND gp.AQ_WorkPersonNum  <> 0
      AND gp.Estimate_ie_Import<> 0
) AS a

UNION ALL

SELECT
    a.creator                                  AS Line,
    a.cus_item_no                              AS Style,
    '2000-01-01 00:00:01.111'                  AS Latest_Activity_Time,
    0                                          AS TieSeamQty,
    0                                          AS Defect_Quantity,
    0                                          AS Net_Good_Qty,
    0.00                                       AS DefectRate,
    0.00                                       AS People,
    0.00                                       AS IE_Seconds,
    0                                          AS WorkSeconds,
    0.00                                       AS RealWorkSeconds,
    0.00                                       AS GroupPercent,
    0                                          AS TargetNum,
    0.00                                       AS Efficiency
FROM #tempALLTieSeam AS a
LEFT JOIN #tempGroupPeople AS b
       ON a.creator = b.A_Line AND a.cus_item_no = b.B_style
WHERE b.B_style IS NULL
   OR b.AQ_WorkPersonNum = 0
   OR b.Estimate_ie_Import = 0

ORDER BY Line;

 """