import json
import uuid
import xlsxwriter
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_file


app = Flask(__name__)

# Use a global variable to store the list of tickets
tickets = []

# Use a global variable to store the login credentials for the admin
admin_credentials = {'username': 'admin', 'password': 'password'}

it_crendentials = {'username' : 'iworkinit', 'password' : 'catsanddogs123'}

# Use a session variable to store the current logged-in user
logged_in_user = None


def generate_identifier():
    random_string = str(uuid.uuid4())[:8] # Generate a random string of 8 characters
    timestamp = datetime.now().strftime('%Y') # Get the current timestamp
    return f"{timestamp}-{random_string}" # Combine the timestamp and random string

def search_for_ticket(identifier):
  for ticket in tickets:
    if ticket['identifier'] == identifier:
      return ticket
  return None

@app.route('/export-to-excel')
def export_to_excel():
  # Get the ticket data from the database

  # Create a new workbook and sheet
  workbook = xlsxwriter.Workbook('tickets.xlsx')
  sheet = workbook.add_worksheet()

  # Add the ticket data to the sheet
  # Add the ticket data to the sheet
  for row_num, data in enumerate(tickets, start=1):
    values = [data['id'], data['identifier'], data['requested_item'], data['department'], data['project'], data['status']]
    sheet.write_row(row_num, 0, values)

  # Close the workbook
  workbook.close()

  # Send the Excel file to the client
  return send_file('tickets.xlsx', as_attachment=True)


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global logged_in_user
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if (username == admin_credentials['username'] and
            password == admin_credentials['password']):
            logged_in_user = username
            return redirect(url_for('show_tickets'))
        else:
            return render_template('login.html', error='Invalid login')
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    global logged_in_user
    logged_in_user = None
    return redirect(url_for('home'))

@app.route('/tickets', methods=['GET', 'POST'])
def show_tickets():
    global tickets
    if request.method == 'POST':
        if logged_in_user:
            requested_item = request.form['requested_item']
            department = request.form['department']
            project = request.form['project']
            if requested_item and department and project:
                ticket = {
                    'requested_item': requested_item,
                    'department': department,
                    'project': project,
                    'id': len(tickets) + 1,  # Assign a unique ID to the ticket
                    'change_log': [],
                    'notes': '',
                    'status': 'Open',  # Add the status field
                    'identifier': ''
                    }
                
                # Add identifier to the ticket
                ticket['identifier'] = generate_identifier()
                # Add creation time to the ticket
                change_log_entry = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'user': logged_in_user,
                    'field': 'created',
                    'old_value': '',
                    'new_value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }
                ticket['change_log'].append(change_log_entry)
                tickets.append(ticket)
                # Write ticket data to the json file
                with open('tickets.json', 'w') as outfile:
                    json.dump(tickets, outfile)
                return redirect(url_for('show_tickets'))
            else:
                return render_template('tickets.html', error='All fields are required', tickets=tickets)
        else:
            return redirect(url_for('login'))
    else:
        if logged_in_user:
            # Only load the tickets from the JSON file if the tickets list is empty
            if not tickets:
                with open('tickets.json') as json_file:
                    old_tickets = json.load(json_file)
                    tickets.extend(old_tickets)
            return render_template('tickets.html', tickets=tickets)
        else:
            return redirect(url_for('login'))


@app.route('/edit-ticket/<int:ticket_id>', methods=['GET', 'POST'])
def edit_ticket(ticket_id):
    # Print the ticket_id variable
    print(f'ticket_id: {ticket_id}')

    # Get the ticket with the specified ID
    ticket = tickets[ticket_id-1]

    if request.method == 'POST':
        # Print the form data
        print(f'form data: {request.form}')

        # Check the notes field
        new_notes = request.form['notes']
        if ticket['notes'] != new_notes:
            # Create a new change log entry
            change_log_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user': logged_in_user,
                'field': 'notes',
                'old_value': ticket['notes'],
                'new_value': new_notes,
            }
            # Append the change log entry to the ticket's change log
            ticket['change_log'].append(change_log_entry)
            ticket['notes'] = new_notes

        # Check the requested_item field
        new_item = request.form['requested_item']
        if ticket['requested_item'] != new_item:
            # Create change log entry
            change_log_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user': logged_in_user,
                'field': 'requested_item',
                'old_value': ticket['requested_item'],
                'new_value': new_item,
            }
            ticket['change_log'].append(change_log_entry)
            ticket['department'] = new_item

        # Check the project field
        new_project = request.form['project']
        if ticket['project'] != new_project:
            # Create change log entry
            change_log_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user': logged_in_user,
                'field': 'project',
                'old_value': ticket['project'],
                'new_value': new_project,
            }
            ticket['change_log'].append(change_log_entry)
            ticket['project'] = new_project

        # Check the status field
        new_status = request.form['status']
        if ticket['status'] != new_status:
            # Create change log entry
            change_log_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user': logged_in_user,
                'field': 'status',
                'old_value': ticket['status'],
                'new_value': new_status,
            }
            ticket['change_log'].append(change_log_entry)
            ticket['status'] = new_status

        # Write ticket data to the json file
        with open('tickets.json', 'w') as outfile:
            json.dump(tickets, outfile)
        return redirect(url_for('show_tickets'))
    else:
        return render_template('edit_ticket.html', ticket=ticket)

@app.route('/search_ticket', methods=['POST'])
def search_ticket():
  # Get the search identifier from the request body
  identifier = request.json['identifier']

  # Search for the ticket in the tickets list
  results = [ticket for ticket in tickets if ticket['identifier'] == identifier]

  # Return the search results to the client
  return jsonify(results)

@app.route('/ticket_details')
def ticket_details():
  identifier = request.args.get('identifier')
  # Search for the ticket
  ticket = search_for_ticket(identifier)
  return render_template('ticket_details.html', ticket=ticket)

if __name__ == '__main__':
    app.run()