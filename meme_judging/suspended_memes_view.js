var meme_statuses = {};
function add_record(record)
{
    let table = document.getElementById("main-table")
    let rowcount = table.rows.length;
    let new_row = table.insertRow(rowcount)
    let id_cell = new_row.insertCell(0);
    let image_cell = new_row.insertCell(1);
    let status_cell = new_row.insertCell(2);
    let author_cell = new_row.insertCell(3);
    id_cell.innerHTML = record.id;
    let img = document.createElement("img");
    img.src = "sus_temp/" + record.filename;
    img.setAttribute("width", "500");
    image_cell.appendChild(img);
    select_status = document.createElement("select");
    let approved_option = document.createElement("option");
    approved_option.value = "approved";
    approved_option.innerHTML = "Approved";
    select_status.appendChild(approved_option);
    select_status.id = "select-status-id" + record.id;
    let suspended_option = document.createElement("option");
    suspended_option.value = "suspended";
    suspended_option.innerHTML = "Suspended";
    select_status.appendChild(suspended_option);
    let banned_option = document.createElement("option");
    banned_option.value = "banned";
    banned_option.innerHTML = "Banned";
    select_status.appendChild(banned_option);
    switch (record.status) {
        case "approved":
            select_status.selectedIndex = 0;
            break;
        case "suspended":
            select_status.selectedIndex = 1;
            break;
        case "banned":
            select_status.selectedIndex = 2;
            break;
    }
    status_cell.appendChild(select_status);
    meme_statuses[record.id] = record.status;
    author_cell.innerHTML = record.author_name + " (" + record.author_id + ")";    
}

function save(filename, data)
{
    let blob = new Blob([data], {type: 'text/csv'});
    if(window.navigator.msSaveOrOpenBlob) {
        window.navigator.msSaveBlob(blob, filename);
    }
    else{
        let elem = window.document.createElement('a');
        elem.href = window.URL.createObjectURL(blob);
        elem.download = filename;        
        document.body.appendChild(elem);
        elem.click();        
        document.body.removeChild(elem);
    }
}

function get_data()
{
    let table = document.getElementById("main-table");
    let ret = "";
    rows = table.rows;
    for (let meme_id in meme_statuses)
    {
        let new_status = document.getElementById("select-status-id" + meme_id).value;
        if (new_status == meme_statuses[meme_id])
        {
            continue;
        }
        ret += meme_id + "=" + new_status + "\n";
    }
    return ret;
}

function download_file()
{
    save("data_to_send.env", get_data());
}

function main()
{
    document.getElementById("download-button").addEventListener("click", download_file);
    images.forEach(record => add_record(record));
}

document.addEventListener("DOMContentLoaded", main);