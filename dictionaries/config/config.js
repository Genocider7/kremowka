const template_file = "../template.dict";
var data = []

function set_rows()
{
    let table = document.getElementById("Main-table");
    let rowcount = table.rows.length;
    for (let i = 0; i < rowcount; i++)
    {
        table.deleteRow(0);
    }
    let counter = 0;
    for (let object of data) {
        let Row = table.insertRow(counter);
        let titlecell = Row.insertCell(0);
        let valuecell = Row.insertCell(1);
        titlecell.id = "TitleCell" + counter.toString();
        valuecell.id = "ValueCell" + counter.toString();
        titlecell.innerHTML = object.title;
        let area = document.createElement("textarea")
        area.id = 'TextArea' + counter.toString();
        area.classList.add('Value-TextArea')
        area.value = object.value;
        valuecell.appendChild(area);
        counter++;
    }
}

function get_data(e)
{
    let file = e.target.files[0];
    if (!file) {
        console.log("test");
        return;
    }
    let reader = new FileReader();
    reader.onload = function(e) {
        data = [];
        let contents = e.target.result;
        data = parse_data(contents);
        document.getElementById("Load-template").value = null;
        set_rows();
    }
    reader.readAsText(file);
}

function parse_data(raw_data)
{
    let lines = raw_data.split("\n");
    result = [];
    for (let line of lines) {
        let temp = line.split("=", 1)
        if (temp.lengths == 0) {
            continue;
        }
        let first = temp[0];
        let second = line.substr(first.length + 1, line.length - first.length - 1);
        let temp_dict = {title: first, value: second};
        result.push(temp_dict);
    }
    return result;
}

function save(filename, data) {
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

function data_to_text()
{
    result = "";
    let i = 0;
    while(true) {
        let el = document.getElementById("TitleCell" + i.toString());
        if (el == null) {
            break;
        }
        result += el.innerHTML + "=";
        el = document.getElementById("TextArea" + i.toString());
        result += el.value.replace("\n", "");
        result += "\n";
        i++;
    }
    return result;
}

function save_dictionary(e)
{
    save("new_dictionary.dict", data_to_text());
}

function main(e)
{
    document.getElementById("Load-template").addEventListener("change", get_data);
    document.getElementById("Save-button").addEventListener("click", save_dictionary);
}

document.addEventListener("DOMContentLoaded", main)