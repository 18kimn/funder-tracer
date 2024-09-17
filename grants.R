library(tidyverse)
library(sysfonts)
library(showtext)
grants <- read_csv("grants.csv")

font_add_google("Lato")
showtext_auto()

total_amount <- grants$funding_amount |> sum(na.rm = T)
total_active <- grants |>
  filter(end_date > lubridate::today()) |>
  pull(funding_amount) |>
  sum(na.rm = T)


unnested_fields <- grants |>
  mutate(fields = str_split(fields, ", ([0-9])*") |>
           map(\(str_vec){
             str_vec |>
               str_remove_all("([0-9])*") |>
               str_trim()
           })) |>
  unnest(fields)

top_active_fields <- unnested_fields |>
  filter(end_date > lubridate::today()) |>
  group_by(fields) |>
  summarize(
    total_funding = sum(funding_amount, na.rm=T),
    total_grants = n()
  ) |>
  arrange(desc(total_funding))

total_current_funding <- unnested_fields |>
  filter(end_date > lubridate::today()) |>
  select(id, funding_amount) |>
  distinct() |>
  pull(funding_amount) |>
  sum()

top_PIs <- unnested_fields |>
  filter(end_date > lubridate::today()) |>
  group_by(researchers) |>
  summarize(total_funding = sum(funding_amount, na.rm=T),
            total_grants = n(),
            fields = paste0(unique(fields), collapse = ", ")) |>
  arrange(desc(total_funding))

depts_by_year <- unnested_fields |>
  mutate(year = lubridate::year(start_date)) |>
  filter(fields %in% top_active_fields$fields[1:7]) |>
  group_by(fields, year) |>
  summarize(total_funding = sum(funding_amount, na.rm=T)) |>
  ggplot(aes(x = year, y = total_funding, color = fields)) +
  geom_line() +
  labs(
    title = "DoD funding by department won in any given year",
    y = NULL,
    x = NULL,
    color = "Fields of research"
  ) +
  scale_y_continuous(labels = scales::label_dollar()) +
  theme_bw(base_family= "Lato", base_size =14)

depts_by_year

sources_by_year <- unnested_fields |>
  mutate(year = lubridate::year(start_date)) |>
  group_by(funding_org_name, year) |>
  summarize(total_funding = sum(funding_amount, na.rm=T)) |>
  ggplot(aes(x = year, y = total_funding, color = str_wrap(funding_org_name, 25))) +
  geom_line() +
  labs(
    title = "DoD funding by department won in any given year",
    y = NULL,
    x = NULL,
    color = "Fields of research"
  ) +
  scale_y_continuous(labels = scales::label_dollar()) +
  theme_bw(base_family= "Lato", base_size =14) +
  theme(
    legend.key.spacing.y = unit(0.3, "cm")
  )

sources_by_year

