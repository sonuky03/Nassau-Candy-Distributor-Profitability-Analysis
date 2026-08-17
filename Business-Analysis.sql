-- Overall Business Performance
SELECT 
    COUNT(*) AS Total_Orders,
    SUM(Sales) AS Total_Sales,
    SUM(Cost) AS Total_Cost,
    SUM(GrossProfit) AS Total_GrossProfit,
    ROUND(SUM(GrossProfit) / SUM(Sales) * 100, 2) AS Overall_Margin_Percentage,
    SUM(Units) AS Total_Units_Sold,
    ROUND(SUM(Sales) / SUM(Units), 2) AS Average_Sales_Per_Unit
FROM
    nassau_candy.candy_sales;
    
    
-- Product Line Profitability Analysis
SELECT
    Division,
    SUM(Sales) AS Total_Sales,
    SUM(Cost) AS Total_Cost,
    SUM(GrossProfit) AS Total_GrossProfit,
    ROUND(SUM(GrossProfit) / SUM(Sales) * 100, 2) AS Profit_Margin_Percentage,
    SUM(Units) AS Total_Units_Sold
FROM nassau_candy.candy_sales
GROUP BY Division
ORDER BY Total_GrossProfit DESC;


-- Product-Level Profitability Analysis
SELECT
    ProductName,
    Division,
    SUM(Sales) AS Total_Sales,
    SUM(Cost) AS Total_Cost,
    SUM(GrossProfit) AS Total_GrossProfit,
    ROUND(SUM(GrossProfit) / SUM(Sales) * 100, 2) AS Profit_Margin_Percentage,
    SUM(Units) AS Total_Units_Sold
FROM nassau_candy.candy_sales
GROUP BY ProductName, Division
ORDER BY Total_GrossProfit DESC;


-- Product Margin Ranking(highest margin to lowest)
SELECT rank() over( order by sum(GrossProfit) / sum(Sales) desc
) as Product_Rank,
    ProductName,
    Division,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(GrossProfit), 2) AS Total_GrossProfit,
    ROUND(SUM(GrossProfit) / SUM(Sales) * 100, 2) AS Profit_Margin_Percentage
FROM nassau_candy.candy_sales
GROUP BY ProductName, Division
ORDER BY Profit_Margin_Percentage DESC;


-- Sales and Margin Performance
SELECT
    ProductName,
    Division,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(GrossProfit), 2) AS Total_GrossProfit,
    ROUND(SUM(GrossProfit) / SUM(Sales) * 100, 2) AS Profit_Margin_Percentage
FROM nassau_candy.candy_sales
GROUP BY ProductName, Division
ORDER BY Total_Sales DESC;


-- Regional Profitability Analysis
SELECT
    Region,
    COUNT(*) AS Total_Transactions,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(Cost), 2) AS Total_Cost,
    ROUND(SUM(GrossProfit), 2) AS Total_GrossProfit,
    ROUND(SUM(GrossProfit) / SUM(Sales) * 100, 2) AS Profit_Margin_Percentage,
    SUM(Units) AS Total_Units_Sold
FROM nassau_candy.candy_sales
GROUP BY Region
ORDER BY Total_GrossProfit DESC;


-- Regional Product Performance
SELECT
    Region,
    ProductName,
    Division,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(GrossProfit), 2) AS Total_GrossProfit,
    ROUND(SUM(GrossProfit) / SUM(Sales) * 100, 2) AS Profit_Margin_Percentage,
    SUM(Units) AS Total_Units_Sold
FROM nassau_candy.candy_sales
GROUP BY Region, ProductName, Division
ORDER BY Region, Total_GrossProfit DESC;


-- High Sales vs Profitability Analysis
SELECT rank() over( order by sum(Sales) desc
) as Product_Rank,
    ProductName,
    Division,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(GrossProfit), 2) AS Total_GrossProfit,
    ROUND(SUM(GrossProfit) / SUM(Sales) * 100, 2) AS Profit_Margin_Percentage,
    SUM(Units) AS Total_Units_Sold
FROM nassau_candy.candy_sales
GROUP BY ProductName, Division
ORDER BY Total_Sales DESC;


-- High Sales vs Margin Classification
WITH Product_Performance AS (
    SELECT
        ProductName,
        Division,
        ROUND(SUM(Sales), 2) AS Total_Sales,
        ROUND(SUM(GrossProfit), 2) AS Total_GrossProfit,
        ROUND(SUM(GrossProfit) / SUM(Sales) * 100, 2) AS Profit_Margin_Percentage
    FROM nassau_candy.candy_sales
    GROUP BY ProductName, Division
),
Benchmarks AS (
    SELECT
        AVG(Total_Sales) AS Avg_Sales,
        AVG(Profit_Margin_Percentage) AS Avg_Margin
    FROM Product_Performance
)
SELECT
    p.ProductName,
    p.Division,
    p.Total_Sales,
    p.Total_GrossProfit,
    p.Profit_Margin_Percentage,
        CASE
        WHEN p.Total_Sales >= b.Avg_Sales
             AND p.Profit_Margin_Percentage >= b.Avg_Margin
            THEN 'High Sales - High Margin'
        WHEN p.Total_Sales >= b.Avg_Sales
             AND p.Profit_Margin_Percentage < b.Avg_Margin
            THEN 'High Sales - Low Margin'
        WHEN p.Total_Sales < b.Avg_Sales
             AND p.Profit_Margin_Percentage >= b.Avg_Margin
            THEN 'Low Sales - High Margin'
        ELSE 'Low Sales - Low Margin'
    END AS Performance_Category
FROM Product_Performance p
CROSS JOIN Benchmarks b
ORDER BY
    p.Total_Sales DESC;
    
    
-- Product Contribution to Total Gross Profit
WITH Product_Profit AS (
    SELECT
        ProductName,
        Division,
        ROUND(SUM(Sales), 2) AS Total_Sales,
        ROUND(SUM(GrossProfit), 2) AS Total_GrossProfit
    FROM nassau_candy.candy_sales
    GROUP BY ProductName, Division
)
SELECT rank() over( order by Total_Grossprofit desc) as Product_Rank,
    ProductName,
    Division,
    Total_Sales,
    Total_GrossProfit,
    ROUND(
        Total_GrossProfit /
        (SELECT SUM(Total_GrossProfit) FROM Product_Profit) * 100,
        2
    ) AS GrossProfit_Contribution_Percentage
FROM Product_Profit
ORDER BY Total_GrossProfit DESC;  


-- Division Contribution to Total Gross Profit
WITH Division_Profit AS (
    SELECT
        Division,
        ROUND(SUM(Sales), 2) AS Total_Sales,
        ROUND(SUM(GrossProfit), 2) AS Total_GrossProfit
    FROM nassau_candy.candy_sales
    GROUP BY Division
)
SELECT
    Division,
    Total_Sales,
    Total_GrossProfit,
    ROUND(
        Total_GrossProfit /
        (SELECT SUM(Total_GrossProfit)
         FROM Division_Profit) * 100,
        2
    ) AS GrossProfit_Contribution_Percentage
FROM Division_Profit
ORDER BY Total_GrossProfit DESC;


-- High Sales but Low Margin Products (Margin Risk)
WITH Product_Performance AS (
    SELECT
        ProductName,
        Division,
        ROUND(SUM(Sales), 2) AS Total_Sales,
        ROUND(SUM(GrossProfit), 2) AS Total_GrossProfit,
        ROUND(
            SUM(GrossProfit) / SUM(Sales) * 100,
            2
        ) AS Profit_Margin_Percentage
    FROM nassau_candy.candy_sales
    GROUP BY ProductName, Division
),
Benchmarks AS (
    SELECT
        AVG(Total_Sales) AS Avg_Sales,
        AVG(Profit_Margin_Percentage) AS Avg_Margin
    FROM Product_Performance
)
SELECT
    p.ProductName,
    p.Division,
    p.Total_Sales,
    p.Total_GrossProfit,
    p.Profit_Margin_Percentage,
    CASE
        WHEN p.Total_Sales >= b.Avg_Sales
             AND p.Profit_Margin_Percentage < b.Avg_Margin
        THEN 'High Sales - Low Margin'
        WHEN p.Total_Sales >= b.Avg_Sales
             AND p.Profit_Margin_Percentage >= b.Avg_Margin
        THEN 'High Sales - High Margin'
        WHEN p.Total_Sales < b.Avg_Sales
             AND p.Profit_Margin_Percentage >= b.Avg_Margin
        THEN 'Low Sales - High Margin'
        ELSE 'Low Sales - Low Margin'
    END AS Performance_Category
FROM Product_Performance p
CROSS JOIN Benchmarks b
ORDER BY
    p.Total_Sales DESC;


-- Low Sales but High Margin Products
-- Potential Growth Opportunities
WITH Product_Performance AS (
    SELECT
        ProductName,
        Division,
        ROUND(SUM(Sales), 2) AS Total_Sales,
        ROUND(SUM(GrossProfit), 2) AS Total_GrossProfit,
        ROUND(
            SUM(GrossProfit) / SUM(Sales) * 100,
            2
        ) AS Profit_Margin_Percentage
    FROM nassau_candy.candy_sales
    GROUP BY ProductName, Division
),
Benchmarks AS (
    SELECT
        AVG(Total_Sales) AS Avg_Sales,
        AVG(Profit_Margin_Percentage) AS Avg_Margin
    FROM Product_Performance
)
SELECT
    p.ProductName,
    p.Division,
    p.Total_Sales,
    p.Total_GrossProfit,
    p.Profit_Margin_Percentage,
    'Low Sales - High Margin' AS Opportunity_Type
FROM Product_Performance p
CROSS JOIN Benchmarks b
WHERE p.Total_Sales < b.Avg_Sales
  AND p.Profit_Margin_Percentage >= b.Avg_Margin
ORDER BY p.Profit_Margin_Percentage DESC;


-- Margin Risk Analysis
-- Identify products with the lowest profit margins
WITH Product_Performance AS (
    SELECT
        ProductName,
        Division,
        ROUND(SUM(Sales), 2) AS Total_Sales,
        ROUND(SUM(Cost), 2) AS Total_Cost,
        ROUND(SUM(GrossProfit), 2) AS Total_GrossProfit,
        ROUND(
            SUM(GrossProfit) / SUM(Sales) * 100,
            2
        ) AS Profit_Margin_Percentage
    FROM nassau_candy.candy_sales
    GROUP BY ProductName, Division
)

SELECT
    ProductName,
    Division,
    Total_Sales,
    Total_Cost,
    Total_GrossProfit,
    Profit_Margin_Percentage,
    
    CASE
        WHEN Profit_Margin_Percentage < 20
            THEN 'Critical Margin Risk'
        WHEN Profit_Margin_Percentage < 40
            THEN 'High Margin Risk'
        WHEN Profit_Margin_Percentage < 50
            THEN 'Moderate Margin Risk'
        ELSE 'Healthy Margin'
    END AS Margin_Risk_Category

FROM Product_Performance
ORDER BY Profit_Margin_Percentage ASC;


-- Cost Efficiency Analysis
-- Identify products where cost consumes a large share of sales
WITH Product_Cost AS (
    SELECT
        ProductName,
        Division,
        ROUND(SUM(Sales), 2) AS Total_Sales,
        ROUND(SUM(Cost), 2) AS Total_Cost,
        ROUND(SUM(GrossProfit), 2) AS Total_GrossProfit
    FROM nassau_candy.candy_sales
    GROUP BY ProductName, Division
)

SELECT
    ProductName,
    Division,
    Total_Sales,
    Total_Cost,
    Total_GrossProfit,

    ROUND(
        Total_Cost / Total_Sales * 100,
        2
    ) AS Cost_to_Sales_Percentage,

    ROUND(
        Total_GrossProfit / Total_Sales * 100,
        2
    ) AS Profit_Margin_Percentage

FROM Product_Cost
ORDER BY Cost_to_Sales_Percentage DESC;