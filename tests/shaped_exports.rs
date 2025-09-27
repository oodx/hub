// Test that shaped exports provide expected items

#[cfg(feature = "serde-derive")]
#[test]
fn test_serde_derive_provides_macros() {
    // Verify Serialize and Deserialize are accessible
    use hub::serde::{Deserialize, Serialize};

    // Type check to verify traits exist
    fn _serialize_check<T: Serialize>(_t: T) {}
    fn _deserialize_check<'de, T: Deserialize<'de>>() {}
}

#[cfg(all(feature = "serde", not(feature = "serde-derive")))]
#[test]
fn test_serde_base_provides_traits() {
    // Just verify the module exists and traits are accessible
    use hub::serde::{Serializer, Deserializer};

    // Type check passes, which means traits are available
    fn _check<S: Serializer, D: Deserializer<'static>>(_s: S, _d: D) {}
}

#[cfg(feature = "json")]
#[test]
fn test_json_convenience_feature() {
    // Verify json convenience feature enables both derive and serde_json
    use hub::serde::{Deserialize, Serialize};
    use hub::serde_json;

    // Type checks - verify traits and functions exist
    fn _has_derive<T: Serialize + for<'de> Deserialize<'de>>(_t: T) {}

    // Verify serde_json functions are accessible
    let _ = serde_json::from_str::<serde_json::Value>;
    let _ = serde_json::to_string::<i32>;
}