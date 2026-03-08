USE job_market;
-- -------------------------------------------------------------------
-- Top Companies
SELECT `Employer Name`,
       COUNT(*) AS job_count,
       ROUND(AVG(`Avg Salary`),2) AS avg_salary
FROM jobs
GROUP BY `Employer Name`
ORDER BY job_count DESC
LIMIT 10;
-- --------------------------------------------------------
-- Remote vs Onsite Jobs
SELECT `Job Is Remote`,
       COUNT(*) AS total_jobs,
       ROUND(AVG(`Avg Salary`),2) AS avg_salary
FROM jobs
GROUP BY `Job Is Remote`;
-- -------------------------------------------------------------
-- Top Cities For Jobs
SELECT `Job City`,
       COUNT(*) AS total_jobs
FROM jobs
WHERE `Job City` != 'Unknown'
GROUP BY `Job City`
ORDER BY total_jobs DESC 
LIMIT 20;
-- -----------------------------------------------------------
-- Salary Ranking by Role
SELECT `Role`,
       `Employer Name`,
       `Avg Salary`,
       RANK() OVER (PARTITION BY `Role` ORDER BY `Avg Salary` DESC) AS salary_rank
FROM jobs
WHERE `Avg Salary` > 0;
-- ---------------------------------------------------------------------
-- Employment Type Breakdown
SELECT `Job Employment Type`,
       `Role`,
       COUNT(*) AS total_jobs
FROM jobs
GROUP BY `Job Employment Type`, `Role`;
-- ---------------------------------------------------------------------
-- Jobs per State (with Average Salary)
SELECT `Job State`,
       COUNT(*) AS total_jobs,
       ROUND(AVG(`Avg Salary`),2) AS avg_salary
FROM jobs
WHERE `Job State` != 'Unknown'
GROUP BY `Job State`
ORDER BY total_jobs DESC;
-- --------------------------------------------------------------------
-- Salary Statistics by Role
SELECT `Role`,
       ROUND(AVG(`Avg Salary`),2) AS mean_salary,
       MAX(`Avg Salary`) AS max_salary,
       MIN(CASE WHEN `Avg Salary` > 0 THEN `Avg Salary` END) AS min_salary
FROM jobs
GROUP BY `Role`;
-- -----------------------------------------------------------------------
-- Cumulative Job Distribution by Role & State
SELECT `Role`,
       `Job State`,
       COUNT(*) AS total_jobs,
       SUM(COUNT(*)) OVER (PARTITION BY `Role` ORDER BY COUNT(*) DESC) AS cumulative_total
FROM jobs
WHERE `Job State` != 'Unknown'
GROUP BY `Role`, `Job State`;
-- -------------------------------------------------------------------------
-- Top 10% Highest Paying Jobs
SELECT *
FROM (
    SELECT `Role`,
           `Employer Name`,
           `Avg Salary`,
           NTILE(10) OVER (PARTITION BY `Role` ORDER BY `Avg Salary` DESC) AS salary_decile
    FROM jobs
    WHERE `Avg Salary` > 0
) t
WHERE salary_decile = 1;
-- --------------------------------------------------------------------------
-- Company Hiring Market Share
SELECT `Employer Name`,
       COUNT(*) AS jobs_posted,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (),2) AS hiring_percentage
FROM jobs
GROUP BY `Employer Name`
ORDER BY jobs_posted DESC
LIMIT 10;
-- --------------------------------------------------------------------------
-- Highest Paying City per Role
SELECT *
FROM (
    SELECT `Role`,
           `Job City`,
           ROUND(AVG(`Avg Salary`),2) AS avg_salary,
           RANK() OVER (PARTITION BY `Role` ORDER BY AVG(`Avg Salary`) DESC) AS rnk
    FROM jobs
    WHERE `Avg Salary` > 0
    GROUP BY `Role`, `Job City`
) t
WHERE rnk = 1;
-- -------------------------------------------------------------------------
-- Role Demand Percentage
SELECT `Role`,
       COUNT(*) AS total_jobs,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (),2) AS demand_percentage
FROM jobs
GROUP BY `Role`
ORDER BY total_jobs DESC;
-- ------------------------------------------------------------------------
-- Top Paying Companies & Job Market Share Analysis by Role
WITH role_salary AS (
    SELECT 
        `Role`,
        `Employer Name`,
        COUNT(*) AS total_jobs,
        ROUND(AVG(`Avg Salary`),2) AS avg_salary
    FROM jobs
    WHERE `Avg Salary` > 0
    GROUP BY `Role`, `Employer Name`
),

ranked_salary AS (
    SELECT 
        `Role`,
        `Employer Name`,
        total_jobs,
        avg_salary,
        RANK() OVER (PARTITION BY `Role` ORDER BY avg_salary DESC) AS salary_rank,
        ROUND(100 * total_jobs / SUM(total_jobs) OVER (PARTITION BY `Role`),2) AS job_share_percentage
    FROM role_salary
)

SELECT *
FROM ranked_salary
WHERE salary_rank <= 5
ORDER BY `Role`, salary_rank;