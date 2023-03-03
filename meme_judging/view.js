let currently_chosen;
let judged_memes = {};

function previous_desired_state()
{
    return currently_chosen > 0;
}

function next_desired_state()
{
    return currently_chosen < images.length - 1;
}

function turn_on_buttons()
{
    let previous_button = document.getElementById("previous-meme-button");
    let next_button = document.getElementById("next-meme-button");
    let approve_button = document.getElementById("approve-button");
    let suspend_button = document.getElementById("suspend-button");
    let ban_button = document.getElementById("ban-button");
    approve_button.disabled = suspend_button.disabled = ban_button.disabled = images.length == 0;
    previous_button.disabled = !previous_desired_state();
    next_button.disabled = !next_desired_state();
}

function change_main_image(src)
{
    image_count_label = document.getElementById("image-to-judge-count");
    image_container = document.getElementById("meme-to-judge");
    image_container.src=src;
    image_count_label.innerHTML = (images.length - Object.keys(judged_memes).length).toString();
}

function previous_meme()
{
    currently_chosen--;
    update_meme();
    turn_on_buttons();
}

function next_meme()
{
    currently_chosen++;
    update_meme();
    turn_on_buttons();
}

function approve_meme()
{
    judged_memes[images[currently_chosen]] = "approved";
    if (next_desired_state())
    {
        next_meme();
    } else 
    {
        update_meme();
    }
}

function suspend_meme()
{
    judged_memes[images[currently_chosen]] = "suspended";
    if (next_desired_state())
    {
        next_meme();
    } else 
    {
        update_meme();
    }
}

function ban_meme()
{
    judged_memes[images[currently_chosen]] = "banned";
    if (next_desired_state())
    {
        next_meme();
    } else 
    {
        update_meme();
    }
}

function update_meme()
{
    if (images.length > 0)
    {
        change_main_image(images[currently_chosen]);
    }
    let temp = "";
    if (images[currently_chosen] in judged_memes)
    {
        switch(judged_memes[images[currently_chosen]])
        {
            case "approved":
                temp = "<label class=\"approved-label\">Approved</label>";
                break;
            case "suspended":
                temp = "<label class=\"suspended-label\">Suspended</label>";
                break;
            case "banned":
                temp = "<label class=\"banned-label\">Banned</label>";
                break;
            default:
                temp = "";
                break;
        }
    }
    temp += "\t" + (currently_chosen + 1).toString() + "/" + images.length.toString();
    document.getElementById("currently-showing").innerHTML = temp;
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

function get_data()
{
    ret = "";
    for (key in judged_memes)
    {
        let value = judged_memes[key];
        let temp_arr = key.split(".");
        temp_arr = temp_arr[0].split("\\");
        let id = temp_arr[temp_arr.length - 1];
        ret += id + "=" + value + "\n";
    }
    return ret;
}

function download_file()
{
    let ok = true;
    if (images.length > Object.keys(judged_memes).length)
    {
        if (!confirm("You haven't judged all of the memes. Are you sure want to download?"))
        {
            ok = false;
        }
    }
    if (ok)
    {
        save("data_to_send.env", get_data());
    }
}

function main()
{
    currently_chosen = 0;
    update_meme();
    turn_on_buttons();
    document.getElementById("previous-meme-button").addEventListener("click", previous_meme);
    document.getElementById("next-meme-button").addEventListener("click", next_meme);
    document.getElementById("approve-button").addEventListener("click", approve_meme);
    document.getElementById("suspend-button").addEventListener("click", suspend_meme);
    document.getElementById("ban-button").addEventListener("click", ban_meme);
    document.getElementById("download-button").addEventListener("click", download_file);
}

document.addEventListener("DOMContentLoaded", main)