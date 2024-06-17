"use server";

const API_URL = "http://192.168.0.66:8000"; // 사용자 정보 GET API URL
const API_URL2 = "http://192.168.0.66:8001" // 자소서페이지 관심직무, 파일첨부 POST 
export async function getUserList(user_id) { // 함수 인자에 user_id 추가
  const res = await fetch(`${API_URL}/get_user/${user_id}`); // 템플릿 리터럴로 user_id 포함

  if (!res.ok) {
    throw new Error("Failed to fetch data");
  }

  const userList = await res.json();

  return userList;
}

