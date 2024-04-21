// maunium-stickerpicker - A fast and simple Matrix sticker picker widget.
// Copyright (C) 2020 Tulir Asokan
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

const widgetId = null; // if you know the widget ID, supply it.
const api = new mxwidgets.WidgetApi(widgetId);


// Before doing anything else, request capabilities:
api.requestCapabilities(mxwidgets.StickerpickerCapabilities);
api.requestCapability(mxwidgets.MatrixCapabilities.MSC4039UploadFile);


// Start the messaging
api.start();

// If waitForIframeLoad is false, tell the client that we're good to go
api.sendContentLoaded();

export function sendSticker(content){
    api.sendSticker(content);
}

export function sendGIF(url){
    // just print out content, should be URL
    console.log("Content:"+url.url);
    return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', url.url, true);
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          const responseData = xhr.responseText;
          // Call uploadFile with response data
          api.uploadFile(responseData)
            .then(result => {
                console.log("Here's the result:"+result);
              resolve(result);
            })
            .catch(error => {
              reject(error);
            });
        } else {
          reject(new Error('Failed to fetch data')); // Reject the outer promise if fetching data fails
        }
      }
    };
    xhr.send();
  }); 
}

/*
 *let widgetId = null
 *
 *window.onmessage = event => {
 *    if (!window.parent || !event.data) {
 *        return
 *    }
 *
 *    const request = event.data
 *    if (!request.requestId || !request.widgetId || !request.action || request.api !== "toWidget") {
 *        return
 *    }
 *
 *    if (widgetId) {
 *        if (widgetId !== request.widgetId) {
 *            return
 *        }
 *    } else {
 *        widgetId = request.widgetId
 *    }
 *
 *    let response
 *
 *    if (request.action === "visibility") {
 *        response = {}
 *    } else if (request.action === "capabilities") {
 *        response = { capabilities: ["m.sticker", "org.matrix.msc4039.upload_file"] }
 *    } else {
 *        response = { error: { message: "Action not supported" } }
 *    }
 *
 *    window.parent.postMessage({ ...request, response }, event.origin)
 *}
 *
 *export function sendSticker(content) {
 *    const data = {
 *        content: { ...content },
 *        // `name` is for Element Web (and also the spec)
 *        // Element Android uses content -> body as the name
 *        name: content.body,
 *    }
 *    // Custom field that stores the ID even for non-telegram stickers
 *    delete data.content.id
 *
 *    // This is for Element iOS
 *    const widgetData = {
 *        ...data,
 *        description: content.body,
 *        file: `${content.id}.png`,
 *    }
 *    // Element iOS explodes if there are extra fields present
 *    delete widgetData.content["net.maunium.telegram.sticker"]
 *
 *    window.parent.postMessage({
 *        api: "fromWidget",
 *        action: "m.sticker",
 *        requestId: `sticker-${Date.now()}`,
 *        widgetId,
 *        data,
 *        widgetData,
 *    }, "*")
 *}
 *
 *export function sendGIF(content) {
 *    const data = {
 *        content: { ...content },
 *        name: content.body,
 *        msgtype: "m.image"
 *    }
 *
 *    delete data.content.id
 *    // This is for Element iOS
 *    const widgetData = {
 *        ...data,
 *        description: content.body,
 *        file: `${content.id}.png`,
 *    }
 *
 *    window.parent.postMessage({
 *        api: "fromWidget",
 *        action: "m.room.message",
 *        requestId: `gif-${Date.now()}`,
 *        widgetId,
 *        data,
 *        widgetData,
 *    }, "*")
 *}
 */
