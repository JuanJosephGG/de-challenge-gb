from sqlalchemy import text
from src.connections.database import engine

# SQL DDL for Requirement 1
VIEW_HIRES_BY_QUARTER = """
CREATE OR REPLACE VIEW view_metrics_hires_by_quarter AS
SELECT 
    d.department,
    j.job,
    SUM(CASE WHEN EXTRACT(QUARTER FROM CAST(he.datetime AS TIMESTAMP)) = 1 THEN 1 ELSE 0 END) AS q1,
    SUM(CASE WHEN EXTRACT(QUARTER FROM CAST(he.datetime AS TIMESTAMP)) = 2 THEN 1 ELSE 0 END) AS q2,
    SUM(CASE WHEN EXTRACT(QUARTER FROM CAST(he.datetime AS TIMESTAMP)) = 3 THEN 1 ELSE 0 END) AS q3,
    SUM(CASE WHEN EXTRACT(QUARTER FROM CAST(he.datetime AS TIMESTAMP)) = 4 THEN 1 ELSE 0 END) AS q4
FROM hired_employees he
JOIN departments d ON he.department_id = d.id
JOIN jobs j ON he.job_id = j.id
WHERE EXTRACT(YEAR FROM CAST(he.datetime AS TIMESTAMP)) = 2021
GROUP BY d.department, j.job
ORDER BY d.department ASC, j.job ASC;
"""

# SQL DDL for Requirement 2
# Note: We use a LEFT JOIN to ensure departments with 0 hires are counted in the global mean calculation.
VIEW_DEPARTMENTS_ABOVE_MEAN = """
CREATE OR REPLACE VIEW view_metrics_departments_above_mean AS
WITH dept_hires AS (
    SELECT 
        d.id,
        d.department,
        COUNT(he.id) AS hired
    FROM departments d
    LEFT JOIN hired_employees he 
        ON d.id = he.department_id 
        AND EXTRACT(YEAR FROM CAST(he.datetime AS TIMESTAMP)) = 2021
    GROUP BY d.id, d.department
),
mean_hires AS (
    SELECT AVG(hired) AS avg_hired FROM dept_hires
)
SELECT 
    dh.id,
    dh.department,
    dh.hired
FROM dept_hires dh
CROSS JOIN mean_hires mh
WHERE dh.hired > mh.avg_hired
ORDER BY dh.hired DESC;
"""

def create_analytics_views():
    """Executes the DDL statements to create materialized/standard views in PostgreSQL."""
    with engine.connect() as conn:
        conn.execute(text(VIEW_HIRES_BY_QUARTER))
        conn.execute(text(VIEW_DEPARTMENTS_ABOVE_MEAN))
        conn.commit()
        print("✅ Analytical Views created successfully in the database.")

if __name__ == "__main__":
    create_analytics_views()