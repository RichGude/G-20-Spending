'''
Author:     Rich Gude
Purpose:    To import data files (csv format) obtained from World Bank website, stored in the local folder,
            and export condensed data tables with missing data expunged or miminally caluclated.
Revision:   1, dated February 13, 2021
'''

# Import Libraries
import os                   # for specifying working directory commands
import pandas as pd         # for csv file reading and dataFrame manipulation
import numpy as np          # for pandas value typing
import openpyxl             # for appending to excel files
import csv                  # for csv file reading and writing

# %% Define a function for condensing data files for each problem statement in the assignment:
'''
Problem Explanation:
The World Bank files contain information from a lot of countries and economic/political unions (e.g., the "Arab World" referring to the members
  of the League of Arab States, as establised in the metadata commentary) from as far back as 1960 to the present (~2020).  Unfortuneately, for
  many countries, many years of data are missing from many of the data sets.  If enough years of data are missing, the analysis of each country
  is essentially meaningless, so those countries must be dropped.  For countries that have only a few years missing, that data can be interpolated.
'''


# Define function for importing data for all charts
def spending_analysis(data_list, file_name, exc_name='spending.xlsx', perc_miss=0.4):
    """
    This function takes in a list of WorldBank files and an allowable tolerance for missing values from each country and
    returns one Excel ('.xlsx') file, titled as exc_name, for additional analysis and visualization.

    :param data_list:   List of file paths for World-Bank-formatted csv files for education/health/military/GDP spending
      First 4 rows are ignorable.  Row 5 contains column headers, Rows 6 to 269 contain countries/unions (264 in total)
      First Column is country name, Columns 5 through 64 contain data from each country from 1960 to 2020
    :param perc_miss:   Fraction of missing values for which a country will be dropped from analysis, 40% by default
      Any country not having at least [60%] of the years between 1960 and 2020 will be dropped from the table.
    :param exc_name:    Excel file name into which all spending sheets will be added, should be standard for all files
    :return:            Excel, '.xlsx', file of spending education/health/military spending metrics
    """

    # Establish data working directory
    dwd = os.path.join(os.getcwd(), 'data')

    # Import each data file from given path in data_list, with row five containing column headers and start of data
    #   Save each file name as the key of a dictionary where the data is the key element.
    try:
        data = {file: pd.read_csv(os.path.join(dwd, file), header=2)
                for file in data_list}
    except:
        # When reading from spending_calc files, some characters are encoded improperly
        data = {file: pd.read_csv(os.path.join(
            dwd, file), header=2, encoding='cp1252') for file in data_list}

    # Drop columns 2 through 4 (unnecessary metadata)
    for file in data_list:
        data[file].drop(columns=data[file].columns[1:4], inplace=True)

    # Despite data repositories being updated 12/2020, many data sets have missing data from 2018, '19 and '20.
    # For this reason, drop the last 4 columns (not 3, since WorldBank comma-separating adds an extra junk column)
    for file in data_list:
        data[file].drop(columns=data[file].columns[-4:], inplace=True)

    # Evaluate the common starting year for each data set:
    col_drop_index = 1
    # For each data set:
    for file in data_list:
        # For each yearly column starting at the lowest year:
        for i in range(1, data[file].shape[1]):
            # If the yearly column is not empty, break out of the last for-loop to save processing time
            if sum(data[file][data[file].columns[i]].isna()) != len(data[file]):
                break
            # Else, if the new index is greater than the oldest saved, save "index"
            elif i > col_drop_index:
                col_drop_index = i
    for file in data_list:
        data[file].drop(
            columns=data[file].columns[1:col_drop_index], inplace=True)
    print(
        f'The \'{file_name}\' data starts in year {1960 + col_drop_index - 1}.')

    # Evaluate whether each country has enough values to be considered relevant for analysis:
    print(
        f'There are {len(data[data_list[0]])} countries/unions within the World Bank datasets prior to NaN analysis.')
    # Use a set to catalogue all indices from each dataset that do not have enough data points
    row_drop_index = set(())
    # For each dataset:
    for file in data_list:
        # For each row (country/union):
        for index, row in data[file].iterrows():
            # Count the number of NaN values in each row, and compare to total length:
            if sum(row.isna())/len(row) > perc_miss:
                # If more than the allowable percentage are missing, add the index to the set of rows to be dropped
                row_drop_index.add(index)

    # Drop all rows to be dropped
    for file in data_list:
        data[file].drop(index=row_drop_index, inplace=True)
    print(
        f'There are {len(data[data_list[0]])} countries/unions within the datasets after NaN analysis.')

    # Fill in NaN (which are the minority of data points) with linearly interpolated data along each country/union:
    for file in data_list:
        # First, momentarily drop the 'countries' column in order to interpolate numeric data
        country_ser = data[file][data[file].columns[0]]
        data[file].drop(columns=data[file].columns[0], inplace=True)

        # Interpolate numeric data (using limit_area to preclude extrapolation of data)
        data[file].interpolate(axis=1, limit_area='inside', inplace=True)

        # Add back country data as the first column (hence, the '0')
        data[file].insert(0, country_ser.name, country_ser)
        # Sort values by '2013' date (since some countries may be missing more recent dates
        data[file].sort_values(by='2013', ascending=False, inplace=True)

    # Verify if spending Excel file already exists in the working directory; if not, create a first instance
    if exc_name not in os.listdir():
        print(f'Creating new \'{exc_name}\' file in working directory,')
        with pd.ExcelWriter(exc_name) as writer:
            for file in data_list:
                data[file].to_excel(writer, sheet_name=file[:-4], index=False)

    # Else, save data to given spending Excel file:
    else:     # for appending new sheets to a given Excel file
        with pd.ExcelWriter(exc_name, engine='openpyxl', mode='a') as writer:
            writer.book = openpyxl.load_workbook(exc_name)
            for file in data_list:
                # Verify that sheets to be added don't already exist:
                if file[:-4] in writer.book:
                    print(
                        f'Sheet \'{file[:-4]}\' already exists in \'{exc_name}\'.')
                else:
                    print(
                        f'Importing \'{file[:-4]}\' sheet into \'{exc_name}\'.')
                    data[file].to_excel(
                        writer, sheet_name=file[:-4], index=False)

    print(f'Successfully imported \'{file_name}\' file and sheets.\n')

# Define function for computing military spending per capita


def spending_calc(perc_gdp, total_gdp, total_pop):
    """
    World Bank information does not have per capita spending data for education and military spending.  Accordingly,
    that data must be computed from known World bank data, namely, the military spending as a percent of GDP, the total
    GDP, and the total population for each World Bank-tracked country/union.

    This function is written to take in any combination of the above three files

    :param perc_gdp:    World-Bank-formatted csv file of spending as a percentage of GDP for each country/union
    :param total_gdp:   World-Bank-formatted csv file of total GDP (current US$) for each country/union
    :param total_pop:   World-Bank-formatted csv file of human population for each country/union
    :return:            World-Bank-formatted csv file of spending (current US$) per capita for each country/union
    """

    # Establish data working directory
    dwd = os.path.join(os.getcwd(), 'data')

    # Ensure that spending per capita file does not already exist in data
    file_name = perc_gdp[:4] + 'ExpendPerCap.csv'
    if file_name in os.listdir(dwd):
        print(f'Deleting old \'{file_name}\' file in working directory,')
        os.remove(os.path.join(dwd, file_name))

    # The order of the data file in processing is important
    data_list = [perc_gdp, total_gdp, total_pop]
    # Import each data file from given path in data_list, with row five containing column headers and start of data
    #   Save each file name as the key of a dictionary where the data is the key element.
    data = {file: pd.read_csv(os.path.join(dwd, file), header=2)
            for file in data_list}

    # Create an output dataframe to be written into a CSV file with all original rows and columns of a WB-formatted csv
    output = data[data_list[0]].copy()

    # For the numerical values (spending as %GDP) within the dataframe, multiple by the total GDP, and divide by the
    #   total population to get 'total spending per capita' values
    # Use 'iloc' for integer-based slicing of the dataframes:
    output.iloc[:, 4:] = data[perc_gdp].iloc[:, 4:] * \
        data[total_gdp].iloc[:, 4:] / data[total_pop].iloc[:, 4:]
    # Change all NaN values to a blank string to match other World Bank files
    output = output.replace(np.nan, '', regex=True)

    # Change the 'Indicator Name' to 'XXXX spending per person (current US$ per capita)'
    output[output.columns[2]] = [
        f'{perc_gdp[:4]} spending per person (current US$ per capita)'] * len(output)
    # Empty the 'Indicator Code' column since the World Bank Indicator code for per capita spending is not known
    output[output.columns[3]] = [''] * len(output)

    # Create output csv file
    with open(os.path.join(dwd, file_name), 'w', newline='') as output_file:
        # Save the first four rows of the csv file for reproducing in output file
        writer = csv.writer(output_file)
        with open(os.path.join(dwd, perc_gdp), 'r') as input_file:
            reader = csv.reader(input_file)
            count = 0
            for row in reader:
                if count == 4:
                    break
                writer.writerow(row)
                count += 1
        # Change writer object to import dictionary values from output
        writer = csv.DictWriter(output_file, fieldnames=output.columns)
        writer.writeheader()
        # Save output as a dictionary for row reading
        records = output.to_dict('record')
        writer.writerows(records)
    print(f'Writing of {file_name} complete')

# Define function for computing change in education and healthcare spending (fixed or percentage)


def change_calc(total_cap, out_type, exc_name='spending.xlsx', perc_miss=0.4):
    """
    World Bank information does not have per capita spending growth data for education and healthcare spending.
    Accordingly, that data must be computed from known World bank data, namely, per capita spending  (current US$) for
    sequential years for each World Bank-tracked country/union.

    This function is written to take in any combination of the above three files

    :param total_cap:   World-Bank-formatted csv file of spending (current US$) per capita for each country/union
    :param out_type:    String object: either 'Percent' for an output file showing percent change in spending per year
                            or 'Fixed' for an output file showing fixed change in spending per year (current US$)
    :param exc_name:    Excel file name into which all spending sheets will be added, should be standard for all files
    :param perc_miss:   Fraction of missing values for which a country will be dropped from analysis, 40% by default
                            Any country not having at least [60%] of the eligible years will be dropped from the table.
    :return:            Excel ('.xlsx') file, with a given name, for additional analysis and visualization.
    """

    # Establish data working directory
    dwd = os.path.join(os.getcwd(), 'data')

    # Generate sheet name for spending change file
    sheet_name = total_cap[:4] + 'ChangePerCap' + out_type

    # Save total_cap name as the working dataframe
    try:
        data = pd.read_csv(os.path.join(dwd, total_cap), header=2)
    except:
        # When reading from spending_calc files, some characters are encoded improperly
        data = pd.read_csv(os.path.join(dwd, total_cap),
                           header=2, encoding='cp1252')

    # Drop columns 2 through 4 (unnecessary metadata)
    data.drop(columns=data.columns[1:4], inplace=True)

    # Despite data repositories being updated 12/2020, many data sets have missing data from 2018, '19 and '20.
    # For this reason, drop the last 4 columns (not 3, since WorldBank comma-separating adds an extra junk column)
    data.drop(columns=data.columns[-4:], inplace=True)

    # Evaluate the common starting year for all countries in the data set:
    col_drop_index = 1
    # For each yearly column starting at the lowest year:
    for i in range(1, data.shape[1]):
        # If the yearly column is not empty, break out of the last for-loop to save processing time
        if sum(data[data.columns[i]].isna()) != len(data):
            break
        # Else, save "index"
        col_drop_index = i
    data.drop(columns=data.columns[1:col_drop_index], inplace=True)
    print(
        f'The \'{sheet_name}\' data starts in year {1960 + col_drop_index - 1}.')

    # Evaluate whether each country has enough values to be considered relevant for analysis:
    print(
        f'There are {len(data)} countries/unions within the World Bank dataset prior to NaN analysis.')
    # Use a set to catalogue all indices from each dataset that do not have enough data points
    row_drop_index = []
    # For each row (country/union):
    for index, row in data.iterrows():
        # Count the number of NaN values in each row, and compare to total length:
        if sum(row.isna()) / len(row) > perc_miss:
            # If more than the allowable percentage are missing, add the index to the set of rows to be dropped
            row_drop_index.append(index)

    # Drop all rows to be dropped
    data.drop(index=row_drop_index, inplace=True)
    print(
        f'There are {len(data)} countries/unions within the dataset after NaN analysis.')

    # Fill in NaN (which are the minority of data points) with linearly interpolated data along each country/union and
    #   calculate either 'fixed' or 'percent' change in per capita spending value:
    # First, momentarily drop the 'countries' column in order to interpolate numeric data
    country_ser = data[data.columns[0]]
    data.drop(columns=data.columns[0], inplace=True)

    # Interpolate numeric data (using limit_area to preclude extrapolation of data)
    data.interpolate(axis=1, limit_area='inside', inplace=True)

    # for each country or union:
    for index, row in data.iterrows():
        # Calculate the change in per capita spending, either percentage or fixed, by moving backwards in years
        for year in range(-1, -len(row), -1):
            if out_type == 'Percent':
                row[year] = (row[year] - row[year-1]) / row[year-1] * 100
            elif out_type == 'Fixed':
                row[year] = row[year] - row[year-1]
            # if the user input the wrong string out_put type, assumed 'Fixed':
            else:
                row[year] = row[year] - row[year-1]
    # Drop the first year, since there is no change data for that year
    data.drop(columns=data.columns[0], inplace=True)

    # Add back country data as the first (hence, the '0') column
    data.insert(0, country_ser.name, country_ser)
    # Sort values by '2013' date (since some countries may be missing more recent dates
    data.sort_values(by='2013', ascending=False, inplace=True)

    # Verify if spending Excel file already exists in the working directory; if not, create a first instance
    if exc_name not in os.listdir():
        print(f'Creating new \'{exc_name}\' file in working directory,')
        with pd.ExcelWriter(exc_name) as writer:
            data.to_excel(writer, sheet_name=sheet_name, index=False)

    # Else, save data to given spending Excel file:
    else:  # for appending new sheets to a given Excel file
        with pd.ExcelWriter(exc_name, engine='openpyxl', mode='a') as writer:
            writer.book = openpyxl.load_workbook(exc_name)
            # Verify that sheets to be added don't already exist:
            if sheet_name in writer.book:
                print(
                    f'Sheet \'{sheet_name}\' already exists in \'{exc_name}\'.')
            else:
                print(f'Importing \'{sheet_name}\' sheet into \'{exc_name}\'.')
                data.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f'Successfully imported \'{exc_name}\' file and sheets.\n')


# %% Compare the spending education, healthcare, and military data to that country’s GDP
''' **Notes**
# Importing data:
We will define a function to take in spending data for education, healthcare, and military as a percent (%) of GDP for
  and various countries along with the given GDP information (which is much more robustly understood and cataloged)

# Variables:
Country
Year
GDP (Absolute Value - $)
Spending (Absolute or %)

# Visuals
The immediate problem is the small values with which we're working.  All values for spending as a percent of GDP are
  small (~1-5% in most cases).  Visually, this is very hard to show the comparison, then, between the full GDP and each
  spending amount.  Accordingly, we will have to have two metrics for GDP and spending (different left/right y-axises if
  a line graph is used, or different coloring and size if an area or geographic visual is used).

# Decision:
Divide and Conquer!  There will be four graphs for each country:
  The first three will be Bubble Charts looking at education, healthcare, and military spending individually.  The
  y-axis will be GDP, the x-axis will be year of data, and the color/size of each data point will be the %GDP of each
  spending

  The second graph will be a Combo Chart looking at all spending ratios collectively with GDP.  The x-axis for each
  graph will relay the year information, while the line graph of the chart will model the GDP and the bar charts will
  show the education, healthcare, and military spending for each year showing comparisons to each other.
'''
# Import Education, Healthcare, and Military spending as a %ofGDP into a GDP_spending.xlsx file:
# This file will be used for the first two "Spending versus GDP" graphics.
spending_analysis(data_list=['educExpendGDP.csv', 'hlthExpendGDP.csv', 'miltExpendGDP.csv', 'totalGDP.csv'],
                  file_name='GDP_spending.xlsx')


# %% Compare the education and health to the overall military spending of the country
''' *Notes
We will define a function that takes in the military, education, and healthcare data each as a percent of all government
  spending.  A fourth 'other' category will be defined that is represents all other spending for thematic purposes.

Much like the previous visualizations, there is a problem with small values with which we're working (~1-5% in cases).
Just then as before, there will be a visual for each year and country with enough data to support a visual: using a pie
  to show the percentage of government spending categories, and a simple numeral to show that total spending total above
  the graph.
A second visual will use an area plot to show the progression of government spending with time and the share of each
  spending category within that total

# Variables:
Country
Year
General government final consumption expenditure  (Absolute Value - $)
Spending (%)  
'''
# Import Education, Healthcare, and Military spending as a %ofGovSpending into a gov_spending.xlsx file:
# This file will be used for the two "Spending versus Government Expenditure" graphics.
spending_analysis(data_list=['educExpendTotExp.csv', 'hlthExpendTotExp.csv', 'miltExpendTotExp.csv', 'totalExp.csv'],
                  file_name='gov_spending.xlsx')

# %% Compare the per-person spending for each category to the per person GDP
''' *Notes
We will define a function that takes in the military, education, and healthcare data each as a percent of all government
  spending per person.  Rather than comparing the education, healthcare, and military spending within countries, we'll
  compare each spending category BETWEEN countries.
  
We'll visualize inter-country (vice intra-country) behavior using histograms (for singe-year views) and candlestick
  graphs (for visualizing the spread of education/healthcare/military per-person spending for multiple countries over a
  time frame).

To do this, we'll run the 'spending_analysis' function on each group of education, healthcare, and military spending,
  vice all three together as previously done, giving three separate Excel files.  The upswing to this is that each
  dataset should have data from more countries and years, since the overlap in data will not need to be between all
  spending categories categories.

# Variables:
Country
Year
General government final consumption expenditure  (Absolute Value per person- $Capita)
Spending (%Capita)  
'''
# Import Education, Healthcare, and Military individual spending as a %GDP Capita into a XXXX_cap_spending.xlsx files:
# This file will be used for the education capita graphics.
spending_calc(perc_gdp='educExpendGDP.csv',
              total_gdp='totalGDP.csv', total_pop='totalPop.csv')
spending_analysis(data_list=['educExpendPerCap.csv', 'GDPperCap.csv'],
                  file_name='educ_cap_spending.xlsx')
# This file will be used for the healthcare capita graphics.
spending_analysis(data_list=['hlthExpendPerCap.csv', 'GDPperCap.csv'],
                  file_name='hlth_cap_spending.xlsx')
# This file will be used for the military capita graphics.
spending_calc(perc_gdp='miltExpendGDP.csv',
              total_gdp='totalGDP.csv', total_pop='totalPop.csv')
spending_analysis(data_list=['miltExpendPerCap.csv', 'GDPperCap.csv'],
                  file_name='milt_cap_spending.xlsx')

# %% Fastest growing countries in healthcare and educational spending in fixed value and in percentage
'''
We will define a function that takes in the education and healthcare per person spending (calculated from the last set)
  and produce two new datasets calculating the total change in each value each year and the proportional (percent)
  change of that total change to the total per person spending value.

Using per person vice total spending because that comparison provides a better narrative; if a country is spending more
  money total on each, but the population is growing proportionally faster than either amount, then the country, in
  essence, is spending less on those things compared to their growing tax basis.
  
We'll visualize inter-country (vice intra-country) behavior using Google geocharts (on a per year basis) and line graphs
  (to show all countries compared to each other over a string of years).

To do this, we'll run the 'spending_analysis' function twice on each group of education and healthcare spending, giving
  four separate Excel files.

# Variables:
Country
Year
Change in general government final consumption expenditure - education (Absolute Value per person- $Capita)
Change in general government final consumption expenditure - healthcare (Absolute Value per person- $Capita)
Percent change in general government final consumption expenditure - education (%)
Percent change in general government final consumption expenditure - healthcare (%)
'''
# Import Education and Healthcare change in individual spending:
#   Education as a percent:
change_calc('educExpendPerCap.csv', 'Percent', perc_miss=0.4)
#   Education as a fixed:
change_calc('educExpendPerCap.csv', 'Fixed', perc_miss=0.4)
#   Healthcare as a percent:
change_calc('hlthExpendPerCap.csv', 'Percent', perc_miss=0.4)
#   Healthcare as a fixed:
change_calc('hlthExpendPerCap.csv', 'Fixed', perc_miss=0.4)
