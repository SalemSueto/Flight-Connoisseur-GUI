import requests
import pandas
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class Search():
    def __init__(self, tequila_api, input_file):
        self.tequila_api = tequila_api
        self.input_file = input_file
        self.save_directory = input_file.rsplit('/', 1)[0]
        self.tequila_location_endpoint = "https://tequila-api.kiwi.com/locations/query?"  # Tequila's Location Endpoint
        self.tequila_search_endpoint = "https://tequila-api.kiwi.com/v2/search"
        self.continue_analysis = True
        # Input Data
        self.flight_data = None
        self.iata_fixed = False
        self.result_message = ""
        self.flight_search_list = []
        # Run
        self.open_input_file()
        self.fill_iata_code()
        self.search_flights()
        self.save_results()

    def open_input_file(self):
        """ Read the Input Data """
        if ".txt" in self.input_file:
            self.flight_data = pandas.read_csv(self.input_file, sep="\t")
        if ".csv" in self.input_file:
            self.flight_data = pandas.read_csv(self.input_file, sep=",")

    def fill_iata_code(self):
        """ Identify Airport IATA code for each departure/arrival city. """
        """ In case of multiple airports in the same city -> choose the one with the highest rank. """
        for idx, row in self.flight_data.iterrows():
            # print(self.flight_data.iloc[idx, 5])
            # From City
            if row.From_IATA == "" or pandas.isna(row.From_IATA):
                self.iata_fixed = True
                tequila_param = {"term": row.From_City, "location_types": "city"}
                tequila_headers = {"apikey": self.tequila_api}
                response = requests.get(url=self.tequila_location_endpoint, params=tequila_param,
                                        headers=tequila_headers)
                response.raise_for_status()
                rank_start = 10000000000
                for n in response.json()["locations"]:
                    if n["country"]["name"] == row.From_Country and n["rank"] < rank_start:
                        self.flight_data.loc[idx, 'From_IATA'] = n["code"]
                        rank_start = n["rank"]
            # To City
            if row.To_IATA == "" or pandas.isna(row.To_IATA):
                self.iata_fixed = True
                tequila_param = {"term": row.To_City, "location_types": "city"}
                tequila_headers = {"apikey": self.tequila_api}
                response = requests.get(url=self.tequila_location_endpoint, params=tequila_param,
                                        headers=tequila_headers)
                response.raise_for_status()
                rank_start = 10000000000
                for n in response.json()["locations"]:
                    if n["country"]["name"] == row.To_Country and n["rank"] < rank_start:
                        self.flight_data.loc[idx, 'To_IATA'] = n["code"]
                        rank_start = n["rank"]

        # Save new flight data in case the IATA codes are fixed
        if self.iata_fixed:
            self.flight_data.to_csv(f"{self.save_directory}/flight_iata_fixed.txt", sep='\t', mode='a', index=None)

    def search_flights(self):
        """ Find Flights filtered by the Max-Price and Max-Transfers. """
        today = datetime.now().strftime("%d/%m/%Y")
        six_months_future = (date.today() + relativedelta(months=+6)).strftime("%d/%m/%Y")

        for idx, row in self.flight_data.iterrows():
            # Tequila Search Request
            tequila_params = {"fly_from": row.From_IATA,
                                  "fly_to": row.To_IATA,
                                  "dateFrom": today,
                                  "dateTo": six_months_future}
            tequila_headers = {"apikey": self.tequila_api}
            response = requests.get(url=self.tequila_search_endpoint, params=tequila_params, headers=tequila_headers)
            response.raise_for_status()
            flight_search_df = pandas.json_normalize(response.json()["data"])

            if flight_search_df.empty:
                self.result_message += f"* {row.From_City}-{row.To_City}: No found flight\n"
            else:
                # Filter for the Max_Price
                flight_search_df = flight_search_df.loc[flight_search_df['price'] <= float(row.Max_Price)]
                # Filter for the number of Transfers
                for idx2, row2 in flight_search_df.iterrows():
                    flight_search_df.loc[idx2, 'transfers'] = len(flight_search_df.loc[idx2, 'route'])
                flight_search_df = flight_search_df.loc[flight_search_df['transfers'] <= int(row.Max_Transfer)]
                if flight_search_df.empty:
                    self.result_message += f"* {row.From_City}-{row.To_City}: 0 flight with the selected filters\n"
                else:
                    self.result_message += f"* {row.From_City}-{row.To_City}: {flight_search_df.shape[0]} flights found\n"
                    self.flight_search_list.append(flight_search_df)

    def save_results(self):
        """ Combine the results from each search & Save the result. """
        now = datetime.now()
        flight_result = ""
        if len(self.flight_search_list) > 0:
            flight_result = self.flight_search_list[0]
            if len(self.flight_search_list) > 1:
                for n in range(1, len(self.flight_search_list)):
                    flight_result = pandas.concat([flight_result, self.flight_search_list[n]], axis=0)

        flight_result.to_csv(f"{self.save_directory}/flight_{now.strftime('%d-%m-%Y_%H-%M-%S')}.txt",
                             sep='\t', mode='a', index=False)

        select_cols = ["id", "cityFrom", "countryFrom.name", "cityTo", "countryTo.name", "utc_departure", "utc_arrival",
                       "bags_price.1", "bags_price.2", "availability.seats", "transfers", "price", "conversion.EUR"]
        flight_result_simple = flight_result[select_cols]
        flight_result_simple.to_csv(f"{self.save_directory}/flight_simple_{now.strftime('%d-%m-%Y_%H-%M-%S')}.txt",
                                    sep='\t', mode='a', index=False)
