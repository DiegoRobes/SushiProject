
// DELETE AN ADDRESS //
function deleteAddress(address_id){
    var url = 'delete_address'

    fetch(url, {
        method: 'POST',
        headers:{
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({'address_id': address_id})
    })
    .then((response) =>{
        return response.json()
    })
    .then((data) =>{
        location.reload()
    })

}
