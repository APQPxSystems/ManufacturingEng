# Import Libraries
import streamlit as st
import sqlite3
import pandas as pd
import altair as alt
from io import StringIO

# App Configurations
st.set_page_config(page_title='ME PDCA', layout='wide')
hide_st_style = """
                <style>
                #MainMenu {visibility:hidden;}
                footer {visibility:hidden;}
                header {visibility:hidden;}
                </style>
                """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Remove top white space
st.markdown("""
        <style>
            .block-container {
                    padding-top: 0rem;
                    padding-bottom: 0rem;
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
        </style>
        """, unsafe_allow_html=True)

# Function to create a database table
def create_table():
    conn = sqlite3.connect('me_pdca.db')
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS pdca
        (id INTEGER PRIMARY KEY,
        task TEXT,
        section TEXT,
        dri TEXT,
        start_date DATE,
        end_date DATE,
        status TEXT,
        remarks TEXT)
        ''')
    conn.commit()
    conn.close()

# Function to insert data into the database
def insert_data(task, section, dri, start_date, end_date, status, remarks):
    conn = sqlite3.connect('me_pdca.db')
    c = conn.cursor()
    
    # Get the maximum ID value from the database
    c.execute("SELECT MAX(id) FROM pdca")
    max_id = c.fetchone()[0]
    
    # Increment the maximum ID value by 1 to generate a new ID
    new_id = max_id + 1 if max_id is not None else 1
    
    c.execute('''
            INSERT INTO pdca (id, task, section, dri, start_date, end_date, status, remarks) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
            (new_id, task, section, dri, start_date, end_date, status, remarks))
    conn.commit()
    conn.close()

# Function to delete data from the database
def delete_data(task_id):
    conn = sqlite3.connect('me_pdca.db')
    c = conn.cursor()
    c.execute('''DELETE FROM pdca WHERE id = ?''', (task_id,))
    conn.commit()
    conn.close()

# Function to update data in the database
def update_data(task_id, task, section, dri, start_date, end_date, status, remarks):
    conn = sqlite3.connect('me_pdca.db')
    c = conn.cursor()
    c.execute('''UPDATE pdca SET task=?, section=?, dri=?, start_date=?, end_date=?, status=?, remarks=? WHERE id=?''',
            (task, section, dri, start_date, end_date, status, remarks, task_id))
    conn.commit()
    conn.close()

# Function to handle file upload and concatenate with the database
def upload_pdca_file(file):
    if file is not None:
        content = file.read().decode('utf-8')  # Decode bytes to string
        # Assuming the file is a CSV file
        uploaded_df = pd.read_csv(StringIO(content))
        
        # Generate unique IDs for the uploaded DataFrame
        last_id = display_data_as_df()['id'].max()
        if pd.isnull(last_id):
            last_id = 0
        else:
            last_id = int(last_id)  # Cast to integer
        uploaded_df['id'] = range(last_id + 1, last_id + 1 + len(uploaded_df))
        
        # Concatenate the uploaded data with the existing database
        concatenated_df = pd.concat([display_data_as_df(), uploaded_df], ignore_index=True)
        # Update the database with concatenated data
        conn = sqlite3.connect('me_pdca.db')
        concatenated_df.to_sql('pdca', conn, if_exists='replace', index=False)
        conn.close()
        st.success('PDCA data uploaded and concatenated successfully.')

# Function to display data from the database as a pandas dataframe
def display_data_as_df():
    conn = sqlite3.connect('me_pdca.db')
    df = pd.read_sql_query("SELECT * FROM pdca", conn)
    conn.close()
    return df

def edit_pdca():
    df = display_data_as_df()
    st.subheader('Edit PDCA Items')
    if not df.empty:
        task_id_to_edit = st.selectbox('Select task to edit', df['id'].tolist())
        selected_task = df[df['id'] == task_id_to_edit].iloc[0]
        edited_task = st.text_area('Edit task', value=selected_task['task'])
        edited_section = st.text_input('Edit Section', value=selected_task['section'])
        edited_dri = st.text_input('Edit DRI', value=selected_task['dri'], max_chars=20)  # Change selectbox to text_input
        edited_start_date = st.date_input('Edit start date', value=pd.to_datetime(selected_task['start_date']))
        edited_end_date = st.date_input('Edit target end date', value=pd.to_datetime(selected_task['end_date']))
        edited_status = st.selectbox('Edit status', ['Open', 'Closed'], index=0 if selected_task['status'] == 'Open' else 1)
        edited_remarks = st.selectbox('Edit remarks', ['On-going', 'Complete', 'Delay'],
                                    index=0 if selected_task['remarks'] == 'On-going' else
                                    1 if selected_task['remarks'] == 'Complete' else 2)
        if st.button('Update Data'):
            update_data(task_id_to_edit, edited_task, edited_section, edited_dri, edited_start_date, edited_end_date,
                        edited_status, edited_remarks)
            st.success('Data updated successfully.')
    else:
        st.info('No PDCA items to edit.')

# Main function to run the streamlit app
def main():
    # App title and info
    st.markdown("<p class='app_sub_title'>MANUFACTURING ENGINEERING DEPARTMENT | SYSTEMS ENGINEERING</p>", unsafe_allow_html=True)
    # Tagline
    st.markdown("<p class='tagline'>Mitigating Encumbrances; Moving towards Excellence</p>", unsafe_allow_html=True)
    st.write('________________________________________________')
    st.markdown("<p class='app_title'>MANUFACTURING ENGINEERING PDCA</p>", unsafe_allow_html=True)
    
    
    # Create table if it doesn't exist
    create_table()
    
    # Select user role
    st.markdown("<p class='app_sub_title'>SELECT USER TYPE TO CONTINUE</p>", unsafe_allow_html=True)
    login_col1, login_col2 = st.columns([1,1])
    with login_col1:
        user_role = st.selectbox('Select user type', ['Viewer', 'Editor'])
    with login_col2:
        user_pass = st.text_input('Input user password', type='password')
    
    # User role -- editor
    if user_role == 'Editor' and user_pass == 'MEadmin':
        
        df = display_data_as_df()
        


        # Choose desired activity
        desired_activity = st.selectbox('What do you want to do?', ['View data', 'Add task', 'Edit task', 'Delete task', 'Upload existing PDCA'])
        st.write('________________________________________________')
        
        if desired_activity == 'View data':
            # Main dashboard chart
            unique_section = df['section'].unique()
            main_chart_section = st.selectbox('Select Section', ['ALL'] + list(unique_section))
            if main_chart_section != 'ALL':
                main_chart_df = df[df['section']==main_chart_section]
                
                main_chart_df = main_chart_df.groupby(['dri', 'remarks']).size().reset_index(name='count')
            else:
                main_chart_df = df.groupby(['dri', 'remarks']).size().reset_index(name='count')

            # Plot using Altair
            main_chart = alt.Chart(main_chart_df).mark_bar().encode(
                x='dri:N',
                y='count:Q',
                color=alt.Color('remarks:N', scale=alt.Scale(domain=['On-going', 'Complete', 'Delay'],
                                                            range=['green', 'blue', 'red']),
                            legend=alt.Legend(title='Remarks'))
            ).properties(
                width=600,
                height=400,
                title='Count of Tasks per DRI'
            )
            st.altair_chart(main_chart, use_container_width=True)
            st.write('________________________________________________')
        
        if desired_activity == 'Add task':
            # Adding data
            st.subheader('Add PDCA Items')
            task = st.text_area('Input new task')
            section_col, dri_col = st.columns([1, 1])
            with section_col:
                section = st.text_input('Input Section')
            with dri_col:
                dri = st.text_input('Input DRI')  

            start_col, end_col = st.columns([1,1])
            with start_col:
                start_date = st.date_input('Select start date')
            with end_col:
                end_date = st.date_input('Select target end date')
            status_col, remarks_col = st.columns([1,1])
            with status_col:
                status = st.selectbox('Select status', ['Open', 'Closed'])
            with remarks_col:
                remarks = st.selectbox('Remarks', ['On-going', 'Complete', 'Delay'])

            if st.button('Add Data'):
                insert_data(task, section, dri, start_date, end_date, status, remarks)
                st.success('Data added successfully.')

        if desired_activity == 'Edit task':
            # Edit PDCA items
            edit_pdca()

        # Add option to upload existing PDCA file
        if desired_activity == 'Upload existing PDCA':
            st.subheader('Upload Existing PDCA')
            uploaded_file = st.file_uploader("Upload PDCA file", type=['csv'])
            if st.button('Concatenate with Database'):
                upload_pdca_file(uploaded_file)

        if desired_activity == 'Delete task':
            # Delete PDCA items
            if not df.empty:
                st.subheader('Delete Task')
                task_id_to_delete = st.selectbox('Select task to delete', df['id'].tolist())
                if st.button('Delete Task'):
                    delete_data(task_id_to_delete)
                    st.success('Task deleted successfully.')
            else:
                st.info('No PDCA items to delete.')
        st.write('________________________________________________')
    
        # Display data from the database as a pandas dataframe
        if st.button('Hide PDCA'):
            pass
        if st.button('View all PDCA items'):
            st.subheader('Process Engineering PDCA Items')
            st.write(df)

    # User role -- viewer
    elif user_role == 'Viewer' and user_pass == 'MEviewer':
        
        # Select SECTION and DRI from unique SECTION and DRI names
        df = display_data_as_df()
        section_list = df['section'].unique()
        dri_list = df['dri'].unique()
        
        selected_section = st.selectbox('Select SECTION', ['All'] + list(section_list))
        selected_dri = st.selectbox('Select DRI', ['All'] + list(dri_list))
        
        st.write('________________________________________________')
        
        # Filter the dataframe based on selected SECTION and DRI
        filtered_df = df
        if selected_section != 'All':
            filtered_df = filtered_df[filtered_df['section'] == selected_section]
        if selected_dri != 'All':
            filtered_df = filtered_df[filtered_df['dri'] == selected_dri]

        # Group by Status and Remarks and count the number of tasks
        grouped_df = filtered_df.groupby(['status', 'remarks']).size().reset_index(name='count')

        # Plot using Altair
        chart = alt.Chart(grouped_df).mark_bar().encode(
            x='count:Q',
            y='status:N',
            color=alt.Color('remarks:N', scale=alt.Scale(domain=['On-going', 'Complete', 'Delay'],
                                                        range=['green', 'blue', 'red']),
                        legend=alt.Legend(title='Remarks'))
        ).properties(
            width=600,
            height=400
        )
        st.altair_chart(chart, use_container_width=True)
        st.write('________________________________________________')

        # Display filtered data from the database based on status and remarks
        status_list = df['status'].unique()
        remarks_list = df['remarks'].unique()

        status_col, remarks_col = st.columns([1,1])
        with status_col:
            selected_status = st.selectbox('Select status', status_list)
        with remarks_col:
            selected_remarks = st.selectbox('Select remarks', remarks_list)

        filtered_dri_df = df[(df['section'] == selected_section) & (df['dri'] == selected_dri) & (df['status'] == selected_status) & (df['remarks'] == selected_remarks)]
        st.write(filtered_dri_df)
        st.write('________________________________________________')



    else:
        st.warning('Please input the correct password for the chosen user type.')

if __name__ == '__main__':
    main()

with open('PDCA/style.css') as f:
    css = f.read()

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
