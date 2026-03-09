// Run only on selected table(s)
var targetTables = Selected.Tables;

if (!targetTables.Any())
{
    // Optional: stop if nothing is selected
    throw new System.InvalidOperationException("Select at least one table before running the script.");
}

foreach (var table in targetTables)
{
    foreach (var column in table.Columns)
    {
        // Only apply to physical (non-calculated) columns
        if (column is DataColumn)
        {
            string originalName = column.Name;

            // Convert snake_case to Title Case with spaces
            string prettyName = System.Globalization.CultureInfo.InvariantCulture.TextInfo
                .ToTitleCase(originalName.Replace("_", " "));

            if (prettyName != originalName)
            {
                column.Name = prettyName;
            }
        }
    }
}
