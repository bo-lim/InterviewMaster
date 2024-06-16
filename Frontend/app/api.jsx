"use server";

const API_URL = "http://192.168.0.66:8000"; // 사용자 정보 GET API URL
const API_URL2 = "http://192.168.0.66:8002" // 자소서페이지 관심직무, 파일첨부 POST 
export async function getUserList(user_id) { // 함수 인자에 user_id 추가
  const res = await fetch(`${API_URL}/getuser/${user_id}`); // 템플릿 리터럴로 user_id 포함

  if (!res.ok) {
    throw new Error("Failed to fetch data");
  }

  const userList = await res.json();

  return userList;
}

// 자소서 페이지 관심직무, 파일첨부 post
//API_URL2
export async function postItv(formData) {
  const user_id = formData.get("user_id");
  const itv_text_url = formData.get("itv_text_url");
  const itv_cate = formData.get("itv_cate");
  const itv_job = formData.get("itv_job");

  try {
    // user_id 전송
    let response = await fetch(`http://192.168.0.66:8002/newitv`, {
      method: "POST",
      headers: {"Content-Type": "application/json",},
      // back에 실제 전달되는 데이터
      body: formData,
    });

    console.log(response)

    if (!response.ok) {
      throw new Error("Failed to post new_itv");
    }

  

    console.log("post itv: 등록완료");
    return "itv 정보 등록 완료";
  } catch (error) {
    console.error("Error:", error);
    return "itv 정보 등록에 실패했습니다.";
  }
}
