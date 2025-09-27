// Test that all module paths work correctly with feature forwarding

#[cfg(feature = "json")]
#[test]
fn test_json_paths() {
    // Direct access
    use hub::serde::{Deserialize, Serialize};
    use hub::serde_json;

    // Via data_ext module
    use hub::data_ext::serde_json as sj;

    // Verify both paths work by calling functions
    let _ = serde_json::from_str::<serde_json::Value>;
    let _ = sj::from_str::<sj::Value>;
}

#[cfg(feature = "serde-derive")]
#[test]
fn test_serde_derive_paths() {
    // Direct access to shaped module
    use hub::serde::{Deserialize, Serialize};

    // Via data_ext
    use hub::data_ext::serde;

    // Verify derive macros accessible from both
    fn _check1<T: Serialize + for<'de> Deserialize<'de>>() {}
    fn _check2<T: serde::Serialize + for<'de> serde::Deserialize<'de>>() {}
}

#[cfg(feature = "serde-json")]
#[test]
fn test_serde_json_without_derive() {
    // Can use serde_json without derive macros
    use hub::serde_json;

    let json = r#"{"name":"test","value":42}"#;
    let parsed: serde_json::Value = serde_json::from_str(json).unwrap();

    assert_eq!(parsed["name"], "test");
    assert_eq!(parsed["value"], 42);
}

#[cfg(feature = "data-ext")]
#[test]
fn test_data_ext_bundle() {
    // data-ext should provide serde-derive + serde-json + base64
    use hub::data_ext::{serde, serde_json, base64};

    // Verify derive available
    fn _check<T: serde::Serialize>() {}

    // Verify functions accessible
    let _ = serde_json::to_string::<i32>;

    // Verify base64 module exists
    let encoded = base64::encode(b"test");
    assert!(!encoded.is_empty());
}