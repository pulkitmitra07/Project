CREATE PROCEDURE GroupPopulationByAgeRange
AS
BEGIN
    SET NOCOUNT ON;

    -- Create a temporary table to store the categorized population data
    CREATE TABLE #TempPopulation (
        AgeRange VARCHAR(20),
        Population INT
    );

    -- Declare variables for age range calculation
    DECLARE @MinAge INT;
    DECLARE @MaxAge INT;
    DECLARE @Increment INT = 5;

    -- Calculate the minimum and maximum age values
    SELECT @MinAge = MIN(CAST(Age AS INT)), @MaxAge = MAX(CAST(Age AS INT))
    FROM DimAge
    WHERE ISNUMERIC(Age) = 1;

    -- Loop through the age range and insert the categorized population data into the temporary table
    WHILE @MinAge <= @MaxAge
    BEGIN
        DECLARE @UpperBound INT = @MinAge + @Increment - 1;
        DECLARE @AgeRange VARCHAR(20) = CONVERT(VARCHAR(10), @MinAge) + '-' + CONVERT(VARCHAR(10), @UpperBound) + ' years old';

        INSERT INTO #TempPopulation (AgeRange, Population)
        SELECT @AgeRange, SUM(Population)
        FROM FactPopulation fp
        INNER JOIN DimAge da ON fp.AgeCode = da.AgeCode
        WHERE ISNUMERIC(da.Age) = 1
          AND CAST(da.Age AS INT) BETWEEN @MinAge AND @UpperBound;

        SET @MinAge = @MinAge + @Increment;
    END;

    -- Select the categorized population data from the temporary table
    SELECT AgeRange, Population
    FROM #TempPopulation;

    -- Drop the temporary table
    DROP TABLE #TempPopulation;
END;


-- Execute the procedure
EXEC GroupPopulationByAgeRange;