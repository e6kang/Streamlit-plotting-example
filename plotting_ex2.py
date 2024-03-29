import numpy as np
import pandas as pd
import seaborn as sns
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
from adjustText import adjust_text

import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

def display_options(df):
        # Get columns with specific dtypes
        all_columns = df.columns.values
        # Get columns with numeric data
        numeric_columns = []
        # Get columns with string data
        alphabetic_columns = []
        short_alpha_columns = []
        short_alpha_columns.append('None')
        
        for col in all_columns:
                if df[col].dtype == object:
                        alphabetic_columns.append(col)
                else:
                        numeric_columns.append(col)

        for alpha in alphabetic_columns:
                if df[alpha].nunique() < 10:
                        short_alpha_columns.append(alpha)
                                
        # Side bar contents
        # Allow user to select rows for annotation
        st.sidebar.subheader("Selection options")
        selection_mode = st.sidebar.radio("Selection Mode", ['single','multiple'], index=1)
    
        use_checkbox = st.sidebar.checkbox("Use check box for selection", value=True)

        if ((selection_mode == 'multiple') & (not use_checkbox)):
                rowMultiSelectWithClick = st.sidebar.checkbox("Multiselect with click (instead of holding CTRL)", value=False)
                if not rowMultiSelectWithClick:
                    suppressRowDeselection = st.sidebar.checkbox("Suppress deselection (while holding CTRL)", value=False)
                else:
                    suppressRowDeselection=False
        st.sidebar.text("_____________________________")


        # Display df with desired options
        
        gb = GridOptionsBuilder.from_dataframe(df)

        # Customize gridOptions
        gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True)
        for col in numeric_columns:
                if df[col].dtype == float:
                        gb.configure_column(col,
                                            type=["numericColumn","numberColumnFilter","customNumericFormat"],
                                            precision = 2)
        
        gb.configure_selection(selection_mode)
        if use_checkbox:
                gb.configure_selection(selection_mode, use_checkbox=True, groupSelectsChildren=True, groupSelectsFiltered=True)
        if ((selection_mode == 'multiple') & (not use_checkbox)):
                gb.configure_selection(selection_mode, use_checkbox=False, rowMultiSelectWithClick=rowMultiSelectWithClick, suppressRowDeselection=suppressRowDeselection)

        gb.configure_grid_options(domLayout='normal')
        gridOptions = gb.build()

        # Allow user to select graph type
        st.sidebar.subheader('Plot options')

        plot_type_menu = ['scatter', 'bar', 'box', 'histogram']
        plot_type_choice = st.sidebar.selectbox('Select a plot type:', plot_type_menu)
        plot_size_slider = st.sidebar.slider('Plot size:', 5, 15)
        f, ax = plt.subplots(figsize = (plot_size_slider, 5))

        ###################################################################################################################################

        #Display the grid
        st.header("Streamlit Ag-Grid")
        
        grid_response = AgGrid(
                df,
                gridOptions=gridOptions,
                height=300,
                data_return_mode='FILTERED_AND_SORTED',
                update_mode='MODEL_CHANGED',
                fit_columns_on_grid_load=False,
                allow_unsafe_jscode=True, #Set it to True to allow jsfunction to be injected
                enable_enterprise_modules=True,
                )

        # Make a few color palettes
        pal_1 = 'Set1'
        pal_2 = 'Paired'
        pal_3 = 'Set2'
        pal_4 = 'Accent'
        pal_5 = 'Set1_r'
        pal_6 = 'Set2_r'

        if plot_type_choice == 'scatter':
                x_menu = all_columns
                y_menu = numeric_columns
                group_menu = short_alpha_columns
                pal_menu = [pal_1, pal_2, pal_3, pal_4, pal_5, pal_6]
                anno_menu = alphabetic_columns
                
                x_selection = st.sidebar.selectbox('x axis:', x_menu)
                y_selection = st.sidebar.selectbox('y axis:', y_menu)
                group_selection = st.sidebar.selectbox('Group by:', group_menu)
                palette_selection = st.sidebar.selectbox('Color palette:', pal_menu)
                anno_selection = st.sidebar.selectbox('Annotate by:', anno_menu)

                # Make scatter plot
                if group_selection != 'None':
                        to_plot = grid_response['data'].dropna(subset = [x_selection, y_selection, group_selection], how = 'any')
                        to_plot = to_plot[to_plot[group_selection]!='nan']
                        g = sns.scatterplot(x = x_selection, y = y_selection, data = to_plot,
                                        ax = ax, s = 100,
                                        hue = group_selection,
                                        palette = sns.color_palette(palette = palette_selection,
                                                                    n_colors = to_plot[group_selection].nunique()))
                        
                else:
                        to_plot = grid_response['data'].copy()
                        g = sns.scatterplot(x = x_selection, y = y_selection, data = df,
                                        ax = ax, s = 100)

                if to_plot[y_selection].dtypes != 'object':
                        ymin = to_plot[y_selection].min()
                        ymax = to_plot[y_selection].max()
                        yrange = ymax - ymin
                        
                if to_plot[x_selection].dtypes != 'object':
                        xmin = to_plot[x_selection].min()
                        xmax = to_plot[x_selection].max()
                        xrange = xmax - xmin

                # Rotate xlabels if data type is string
                if to_plot[x_selection].dtypes == 'object':
                        plt.xticks(rotation = 90)
                        print(to_plot[x_selection].dtypes)

                # Set x and y limits
                else:
                        #ax.set_xlim([xmin - 10*math.ceil(abs(xmin)), xmax*1.1])
                        #ax.set_ylim([ymin - 10*math.ceil(abs(ymin)), ymax*1.1])
                        ax.set_xlim([xmin - 0.2*xrange, xmax + 0.2*xrange])
                        ax.set_ylim([ymin - 0.2*yrange, ymax + 0.2*yrange])
                        

                        #ax.set_xlim([-595.24, 3710.04])
                        #ax.set_ylim([-0.4412576956904136, 9.47076517150396])

                if '%' in y_selection and ymax < 20:
                        ax.set_ylim([0, 100])

                # Annotate data points
                anno_ls = []
                selected = grid_response['selected_rows']
                selected_df = pd.DataFrame(selected)
                potential_annos = to_plot[anno_selection].tolist()
                
                for k, v in selected_df.iterrows():
                        if v[x_selection] != 'nan' and v[anno_selection] in potential_annos:
                                anno = ax.text(x = v[x_selection], y = v[y_selection],
                                               s = v[anno_selection], size = 10)
                                anno_ls.append(anno)
                        
                adjust_text(anno_ls, to_plot[x_selection].tolist(), to_plot[y_selection].tolist(),
                            arrowprops=dict(arrowstyle="-", color='k', alpha = 0.5),
                            ax = ax)

                plt.legend(loc = 'upper left', bbox_to_anchor = (1.01, 1.02), title = group_selection)
                                

                st.pyplot(f)

        if plot_type_choice == 'bar':
                x_menu = alphabetic_columns
                y_menu = numeric_columns
                group_menu = short_alpha_columns
                pal_menu = [pal_1, pal_2, pal_3, pal_4, pal_5, pal_6]
                
                x_selection = st.sidebar.selectbox('x axis:', x_menu)
                y_selection = st.sidebar.selectbox('y axis:', y_menu)
                group_selection = st.sidebar.selectbox('Group by:', group_menu)
                palette_selection = st.sidebar.selectbox('Color palette:', pal_menu)

                # Make a bar chart
                if group_selection != 'None':
                        sns.barplot(x = x_selection, y = y_selection, data = df,
                                    ax = ax,
                                    hue = group_selection,
                                    palette = sns.color_palette(palette = palette_selection,
                                                                n_colors = df[group_selection].nunique()))
                else:
                        sns.barplot(x = x_selection, y = y_selection, data = df,
                                    ax = ax)
                                

                plt.xticks(rotation = 90)
                plt.legend(bbox_to_anchor = (1.01,1), title = group_selection)
                st.pyplot(f)
                
        if plot_type_choice == 'box':
                x_menu = alphabetic_columns
                y_menu = numeric_columns
                group_menu = short_alpha_columns
                pal_menu = [pal_1, pal_2, pal_3, pal_4, pal_5, pal_6]
                anno_menu = alphabetic_columns
                
                x_selection = st.sidebar.selectbox('x axis:', x_menu)
                y_selection = st.sidebar.selectbox('y axis:', y_menu)
                group_selection = st.sidebar.selectbox('Group by:', group_menu)
                palette_selection = st.sidebar.selectbox('Color palette:', pal_menu)
                anno_selection = st.sidebar.selectbox('Annotate by:', anno_menu)

                # Make a boxplot
                to_plot = grid_response['data'].dropna(subset = [x_selection, y_selection, group_selection], how = 'any')
                if group_selection == 'None':
                        sns.boxplot(x = x_selection, y = y_selection, data = to_plot,
                                    ax = ax, linewidth = 1, color = 'white', saturation = 1)

                        sns.swarmplot(x = x_selection, y = y_selection, data = to_plot,
                                      ax = ax, edgecolor = 'black', linewidth = 1, size = 8)
                else:
                        sns.boxplot(x = x_selection, y = y_selection, data = to_plot,
                                    ax = ax, linewidth = 1, color = 'white', saturation = 1)
                        
                        sns.swarmplot(x = x_selection, y = y_selection, data = to_plot,
                                      hue = group_selection, size = 8,
                                      ax = ax)
                        plt.legend(loc = 'upper left', bbox_to_anchor = (1.01, 1.02), title = group_selection)

                plt.xticks(rotation = 90)
                tick_labels = ax.get_xticklabels()
                tick_dict = {}
                for i in tick_labels:
                        tick_dict[i.get_text()] = i.get_position()[0]

                # Annotate data points
                anno_ls = []
                selected = grid_response['selected_rows']
                selected_df = pd.DataFrame(selected)
                for k, v in selected_df.iterrows():
                        if v[x_selection] != 'nan':
                                anno = ax.text(x = tick_dict[v[x_selection]], y = v[y_selection],
                                               s = v[anno_selection], size = 10)
                                anno_ls.append(anno)
                        
                all_x = [tick_dict[x] for x in to_plot[x_selection].tolist()]
                adjust_text(anno_ls,
                            all_x,
                            to_plot[y_selection].tolist(),
                            ax = ax)
                        
                st.pyplot(f)
                        
        if plot_type_choice == 'histogram':
                x_menu = numeric_columns
                x_selection = st.sidebar.selectbox('x axis:', x_menu)
                bin_slider = st.slider('Number of bins:', 1, 35, 5)

                # Round values to get general range
                x_min = df[x_selection].min()
                x_max = df[x_selection].max()
                x_range = x_max - x_min
                if x_range >= 1000:
                        x_min = round(x_min, -2)
                        x_max = round(x_max, -2)
                        x_range = x_max-x_min
                else:
                        x_min = round(x_min)
                        x_max = round(x_max)
                        x_range = x_max-x_min

                # Make histogram
                bins = np.histogram_bin_edges(df[x_selection], bins=bin_slider)
                print(bins)
                sns.histplot(data = df, x = x_selection, bins = bin_slider)
                st.pyplot(f)

###################################################################################################################################
# Main function
###################################################################################################################################

def main():

        st.title('Plotting from pandas df')
        
        # Have user upload a file to plot
        data_file = st.file_uploader('Upload CSV or Excel file', type = ['csv', 'xlsx', 'xls'])

        if data_file is not None:
                # To see details
                file_details = {'filename': data_file.name,
                                'filetype': data_file.type,
                                'filesize': data_file.size}
                
                data_file_name = data_file.name.split('.')[0]
                if data_file.name.endswith('csv'):
                        df = pd.read_csv(data_file)
                elif data_file.name.endswith('xlsx') or data_file.name.endswith('xls'):
                        df = pd.ExcelFile(data_file).parse()
                                
                display_options(df)
                 
if __name__ == '__main__':
	main()
