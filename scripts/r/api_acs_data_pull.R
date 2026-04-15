# ACS Data Pull for Montgomery County, Alabama

# tidycensus package to retrieve demographic variables

library(tidycensus)
library(tidyverse)
library(sf)
library(tigris)

# API Key in gitignore file natively on machine

# defining Montgomery County FIPS

AL_FIPS <- "01"
MONTGOMERY_FIPS <- "101"
MONTGOMERY_COUNTY_FIPS <- paste0(AL_FIPS, MONTGOMERY_FIPS)

# defining ACS variables to retrieve
# using 2020-2024 5-year ACS

ACS_YEAR <- 2024
ACS_SURVEY <- "acs5"

# variables dictionary

acs_variables <- c(
  
  # population totals
  
  total_pop = "B01001_001",
  
  # race (non-Hispanic)
  
  white_alone = "B02001_002",
  black_alone = "B02001_003",
  asian_alone = "B02001_005",
  hispanic_total = "B03002_012",
  
  # economic indicators
  
  median_income = "B19013_001",
  poverty_total = "B17001_001",
  poverty_below = "B17001_002",
  
  # transportation access
  
  total_households = "B25044_001",
  no_vehicle = "B25044_003",
  
  # educational attainment (proxy for socioeconomic status)
  
  pop_25_plus = "B15003_001",
  bachelors_plus = "B15003_022"
)

# function to retrieve ACS data at tract level

get_montgomery_tract_data <- function() {
  
  # tract-level data
  
  tract_data <- get_acs(
    geography = "tract",
    variables = acs_variables,
    state = AL_FIPS,
    county = MONTGOMERY_FIPS,
    year = ACS_YEAR,
    survey = ACS_SURVEY,
    geometry = TRUE,
    output = "wide"
  )
  
  # derived percentages
  
  tract_data <- tract_data %>%
    mutate(
      # race/ethnicity percentages
      
      pct_black = (black_aloneE / total_popE) * 100,
      pct_white = (white_aloneE / total_popE) * 100,
      pct_hispanic = (hispanic_totalE / total_popE) * 100,
      
      # poverty rate
      
      pct_poverty = (poverty_belowE / poverty_totalE) * 100,
      
      # no vehicle access rate
      
      pct_no_vehicle = (no_vehicleE / total_householdsE) * 100,
      
      # bachelor's degree attainment
      
      pct_bachelors = (bachelors_plusE / pop_25_plusE) * 100,
      
      # margin of error checks -> flag high MOE tracts
      
      high_moe_flag = ifelse(total_popM / total_popE > 0.15, 1, 0)
    )
  
  return(tract_data)
}

# function to retrieve block group level data

get_montgomery_bg_data <- function() {
  
  bg_data <- get_acs(
    geography = "block group",
    variables = acs_variables,
    state = AL_FIPS,
    county = MONTGOMERY_FIPS,
    year = ACS_YEAR,
    survey = ACS_SURVEY,
    geometry = TRUE,
    output = "wide"
  )
  
  bg_data <- bg_data %>%
    mutate(
      pct_black = (black_aloneE / total_popE) * 100,
      pct_poverty = (poverty_belowE / poverty_totalE) * 100,
      pct_no_vehicle = (no_vehicleE / total_householdsE) * 100,
      high_moe_flag = ifelse(total_popM / total_popE > 0.15, 1, 0)
    )
  
  return(bg_data)
}

# function to create vulnerability index
# help find communities that SPLC has flagged as particularly at-risk

calculate_vulnerability_index <- function(data) {
  
  data <- data %>%
    mutate(
      # vulnerability components (z-score normalized)
      
      z_pct_black = scale(pct_black)[,1],
      z_pct_poverty = scale(pct_poverty)[,1],
      z_pct_no_vehicle = scale(pct_no_vehicle)[,1],
      
      # composite vulnerability index (equal weights)
      
      vulnerability_index = (z_pct_black + z_pct_poverty + z_pct_no_vehicle) / 3,
      
      # categorize vulnerability levels
      
      vulnerability_category = case_when(
        vulnerability_index > 1.0 ~ "High",
        vulnerability_index > 0.0 ~ "Moderate",
        vulnerability_index > -1.0 ~ "Low",
        TRUE ~ "Very Low"
      )
    )
  
  return(data)
}

# execution function

main <- function() {
  cat("Retrieving Montgomery County ACS data...\n")
  
  # getting tract data
  
  cat("Tract-level data\n")
  tract_data <- get_montgomery_tract_data()
  tract_data <- calculate_vulnerability_index(tract_data)
  
  # getting block group data
  
  cat("Block group-level data\n")
  bg_data <- get_montgomery_bg_data()
  bg_data <- calculate_vulnerability_index(bg_data)
  
  # saving to CSV (without geometry for non-spatial use)
  
  tract_df <- tract_data %>% st_drop_geometry()
  bg_df <- bg_data %>% st_drop_geometry()
  
  write_csv(tract_df, "data/census/processed/montgomery_demographics_tract.csv")
  write_csv(bg_df, "data/census/processed/montgomery_demographics_bg.csv")
  
  # saving spatial data as GeoJSON (spatial use)
  
  st_write(tract_data, "data/census/processed/montgomery_demographics_tract.geojson", 
           delete_dsn = TRUE)
  st_write(bg_data, "data/census/processed/montgomery_demographics_bg.geojson",
           delete_dsn = TRUE)
  
  cat("\nACS Data:\n")
  cat("Tracts:", nrow(tract_data), "\n")
  cat("Block Groups:", nrow(bg_data), "\n")
  
  # summary statistics
  
  cat("\nMontgomery County Demographic Summary:\n")
  cat(sprintf("Total Population: %s\n", 
              format(sum(tract_data$total_popE, na.rm=TRUE), big.mark=",")))
  cat(sprintf("Black/African American: %.1f%%\n", 
              mean(tract_data$pct_black, na.rm=TRUE)))
  cat(sprintf("Below Poverty: %.1f%%\n", 
              mean(tract_data$pct_poverty, na.rm=TRUE)))
  cat(sprintf("No Vehicle Access: %.1f%%\n", 
              mean(tract_data$pct_no_vehicle, na.rm=TRUE)))
}

# main function
main()
