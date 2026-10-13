using NUnit.Framework;
using MCPForUnity.Editor.Helpers;
using MCPForUnity.Editor.Constants;
using UnityEditor;

namespace MCPForUnityTests.Editor.Helpers
{
    public class AssetPathUtilityOfflineTests
    {
        private bool _originalForceRefresh;

        [SetUp]
        public void SetUp()
        {
            _originalForceRefresh = EditorPrefs.GetBool(EditorPrefKeys.DevModeForceServerRefresh, false);
        }

        [TearDown]
        public void TearDown()
        {
            EditorPrefs.SetBool(EditorPrefKeys.DevModeForceServerRefresh, _originalForceRefresh);
        }

        [Test]
        public void ForkDefaultServerPackageSource_PointsAtSlimPinnedServerCommit()
        {
            string originalOverride = EditorPrefs.GetString(EditorPrefKeys.GitUrlOverride, "");
            try
            {
                EditorPrefs.DeleteKey(EditorPrefKeys.GitUrlOverride);
                string source = AssetPathUtility.GetMcpServerPackageSource();

                Assert.AreEqual(
                    "git+https://github.com/TobiDevTools/unity-mcp.git@90a61162513ab3143b6dce3c637e8799e19dab27",
                    source);
                Assert.IsFalse(source.Contains("subdirectory=Server"),
                    "The slim tree must install from its root.");
            }
            finally
            {
                EditorPrefs.SetString(EditorPrefKeys.GitUrlOverride, originalOverride);
            }
        }

        [Test]
        public void ExplicitServerSourceOverride_TakesPrecedenceOverForkDefault()
        {
            string originalOverride = EditorPrefs.GetString(EditorPrefKeys.GitUrlOverride, "");
            try
            {
                EditorPrefs.SetString(EditorPrefKeys.GitUrlOverride, "mcpforunityserver==10.3.0");
                Assert.AreEqual("mcpforunityserver==10.3.0",
                    AssetPathUtility.GetMcpServerPackageSource());
            }
            finally
            {
                EditorPrefs.SetString(EditorPrefKeys.GitUrlOverride, originalOverride);
            }
        }

        [Test]
        public void ShouldUseUvxOffline_WhenForceRefreshEnabled_ReturnsFalse()
        {
            EditorPrefs.SetBool(EditorPrefKeys.DevModeForceServerRefresh, true);
            Assert.IsFalse(AssetPathUtility.ShouldUseUvxOffline());
        }

        [Test]
        public void ShouldUseUvxOffline_DoesNotThrow()
        {
            EditorPrefs.SetBool(EditorPrefKeys.DevModeForceServerRefresh, false);
            Assert.DoesNotThrow(() => AssetPathUtility.ShouldUseUvxOffline());
        }
    }
}
